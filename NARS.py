import pickle
import random
import time

import Config
import InputBuffer
import NARSGUI
import NARSInferenceEngine
import NALGrammar
import NALSyntax
import NARSMemory

import NARSDataStructures
import Global

"""
    Author: Christian Hahm
    Created: October 8, 2020
    Purpose: NARS definition
"""


class NARS:
    """
       NARS Class
    """
    def __init__(self):
        self.experience_task_buffer = NARSDataStructures.Buffer(item_type=NARSDataStructures.Task)
        self.sensorimotor_event_buffer = NARSDataStructures.EventBuffer(item_type=NARSDataStructures.Task,capacity=10)
        self.memory = NARSMemory.Memory()
        self.delay = 0 # delay between cycles

    def save_memory_to_disk(self, filename="memory.nars"):
        """
            Save the NARS Memory instance to disk
        """
        with open(filename, "wb") as f:
            NARSGUI.NARSGUI.print_to_output("SAVING SYSTEM MEMORY TO FILE: " + filename)
            pickle.dump(self.memory, f, pickle.HIGHEST_PROTOCOL)
            NARSGUI.NARSGUI.print_to_output("SAVE MEMORY SUCCESS")

    def load_memory_from_disk(self, filename="memory.nars"):
        """
            Load a NARS Memory instance from disk.
            This will override the NARS' current memory
        """
        try:
            with open(filename, "rb") as f:
                NARSGUI.NARSGUI.print_to_output("LOADING SYSTEM MEMORY FILE: " + filename)
                # load memory from file
                self.memory = pickle.load(f)
                # Print memory contents to internal data GUI
                if Global.Global.gui_use_internal_data:
                    NARSGUI.NARSGUI.clear_output_gui(data_structure=self.memory.concepts_bag)
                    for item in self.memory.concepts_bag:
                        if item not in self.memory.concepts_bag:
                            NARSGUI.NARSGUI.print_to_output(msg=str(item), data_structure=self.memory.concepts_bag)

                if Global.Global.gui_use_interface:
                    NARSGUI.NARSGUI.gui_total_cycles_lbl.config(text="Cycle #" + str(self.memory.current_cycle_number))

                NARSGUI.NARSGUI.print_to_output("LOAD MEMORY SUCCESS")
        except:
            NARSGUI.NARSGUI.print_to_output("LOAD MEMORY FAIL")

    def run(self):
        """
            Infinite loop of working cycles
        """
        while True:
            # global parameters
            while Global.Global.paused:
                time.sleep(0.2)

            if self.delay > 0:
                time.sleep(self.delay)

            self.do_working_cycle()

    def do_working_cycle(self):
        """
            Performs 1 working cycle.
            In each working cycle, NARS either *Observes* OR *Considers*:
        """
        if Global.Global.gui_use_interface:
            NARSGUI.NARSGUI.gui_total_cycles_lbl.config(text="Cycle #" + str(self.memory.current_cycle_number))

        InputBuffer.process_next_pending_sentence()

        self.Process_Sensorimotor_Buffer()

        rand = random.random()
        if rand < Config.MINDFULNESS and len(self.experience_task_buffer) > 0:
            # OBSERVE
            self.Observe()
        else:
            # CONSIDER
            self.Consider()

        self.memory.current_cycle_number += 1

    def do_working_cycles(self, cycles: int):
        """
            Performs an arbitrary number of working cycles.
        """
        for i in range(cycles):
            self.do_working_cycle()

    def Process_Sensorimotor_Buffer(self):
        """
            Process sensorimotor events into the experience buffer
        """
        if len(self.sensorimotor_event_buffer) > 1: # need multiple events to process implications
            event_task_A = self.sensorimotor_event_buffer.take().object # take an event from the buffer
            event_A = event_task_A.sentence

            event_task_B = self.sensorimotor_event_buffer.take().object # take another event from the buffer
            event_B = event_task_B.sentence

            # insert the events
            self.experience_task_buffer.put_new(event_task_A)
            self.experience_task_buffer.put_new(event_task_B)

            # do temporal inference
            derived_sentences = NARSInferenceEngine.do_temporal_inference_two_premise(event_A,event_B)

            # insert the derived knowledge
            for derived_sentence in derived_sentences:
                self.experience_task_buffer.put_new(NARSDataStructures.Task(derived_sentence))




    def Observe(self):
        """
            Process a task from the experience buffer
        """
        task_item = self.experience_task_buffer.take()

        if task_item is None:
            return  # nothing to observe

        # process task
        self.process_task(task_item.object)

        if isinstance(task_item.object.sentence, NALGrammar.Question) and task_item.object.needs_to_be_answered_in_output:
            # decay priority
            task_item.decay()

            # return task to buffer
            self.experience_task_buffer.put(task_item)


    def Consider(self):
        """
            Process a random belief from a concept in memory
        """

        concept_item = self.memory.get_concept()

        if concept_item is None:
            return  # nothing to ponder

        # remove from GUI
        if Global.Global.gui_use_internal_data:
            NARSGUI.NARSGUI.remove_from_output(str(concept_item), data_structure=self.memory.concepts_bag)

        if isinstance(concept_item.object.term, NALGrammar.StatementTerm):
            # Concept is S --> P
            concept_to_consider = concept_item.object
        else:
            # Concept is S or P
            related_concept = self.memory.get_semantically_related_concept(concept_item.object)
            concept_to_consider = related_concept

        if concept_to_consider is not None:
            sentence = concept_to_consider.belief_table.peek() # get most confident belief
            if sentence is not None:
                # process the judgment
                self.process_judgment_sentence(sentence)

         # decay priority
        concept_item.decay()
        # print back to GUI
        if Global.Global.gui_use_internal_data:
            NARSGUI.NARSGUI.print_to_output(str(concept_item), data_structure=self.memory.concepts_bag)


    def process_task(self, task: NARSDataStructures.Task):
        """
            Processes any Narsese task
        """
        NARSDataStructures.assert_task(task)

        if task.sentence.punctuation == NALSyntax.Punctuation.Question or NALGrammar.VariableTerm.QUERY_SYM in str(task.sentence.statement.term):
            self.process_question(task)
        elif task.sentence.punctuation == NALSyntax.Punctuation.Judgment:
            self.process_judgment_task(task)

    def process_judgment_task(self, task: NARSDataStructures.Task):
        """
            Processes a Narsese Judgment Task

            :param Judgment Task to process
        """
        NARSDataStructures.assert_task(task)

        j1 = task.sentence

        # get terms from sentence
        statement_term = j1.statement.term

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        if statement_term.contains_variable(): return #todo handle variables
        
        if task.needs_initial_processing:
            """
                Initial Processing
                
                Revise this judgment with the most confident belief, then insert it into the belief table
            """
            if task.is_from_input:
                derived_sentences = NARSInferenceEngine.do_inference_one_premise(j1)
                for derived_sentence in derived_sentences:
                    self.experience_task_buffer.put(NARSDataStructures.Task(derived_sentence))

            # revise the judgment
            self.process_judgment_sentence(j1, statement_concept)
            # add the judgment itself into concept's belief table
            statement_concept.belief_table.put(j1)
            task.needs_initial_processing = False
        else:
            """
                Continued processing
                
                Do local/forward inference on a related belief
            """
            self.process_judgment_sentence(j1)


    def process_judgment_sentence(self, j1, related_concept=None):
        """
            Processes a Judgment Sentence with a belief from a related concept.

            :param j1 - judgment sentence to process
            :param related_concept - (Optional) concept to process the judgment with

            #todo handle variables
            #todo handle tenses
        """
        statement_term = j1.statement.term
        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        if statement_term.contains_variable(): return

        if related_concept is None: # get a related concept
            related_concept = self.memory.get_semantically_related_concept(statement_concept)
            if related_concept is None:
                print("none!")
                return  # no related concepts!

        # check for a belief we can interact with
        j2 = None
        for (belief, confidence) in related_concept.belief_table:
            if not NALGrammar.Sentence.may_interact(j1,belief): continue
            j2 = belief # belief can interact with j1

        if j2 is None: return  # done if can't interact

        derived_sentences = NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)
        for derived_sentence in derived_sentences:
            self.experience_task_buffer.put(NARSDataStructures.Task(derived_sentence))

    def process_question(self, task):
        """
            Process a Narsese question task

            Get the best answer to the question if it's known and perform inference with it;
            otherwise, use backward inference to derive new questions that could lead to an answer.

            #todo handle variables
            #todo handle tenses
        """
        NARSDataStructures.assert_task(task)

        # get terms from sentence
        statement_term = task.sentence.statement.term

        if statement_term.contains_variable(): return  # todo handle variables

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        # get the best answer from concept belief table
        best_answer: NALGrammar.Judgment = statement_concept.belief_table.peek_max()
        j1 = None
        if best_answer is not None:
            #
            # Answer the question
            #
            if task.is_from_input and task.needs_to_be_answered_in_output:
                NARSGUI.NARSGUI.print_to_output("OUT: " + best_answer.get_formatted_string())
                task.needs_to_be_answered_in_output = False

            # do inference between answer and a related belief
            j1 = best_answer
        else:
            # do inference between question and a related belief
            j1 = task.sentence

        # get a related concept
        related_concept = self.memory.get_semantically_related_concept(statement_concept)
        if related_concept is None: return  # no related concepts!

        # check for a belief we can interact with
        j2 = None
        for (belief,confidence) in related_concept.belief_table:
            if not NALGrammar.Sentence.may_interact(j1,belief): continue
            j2 = belief # belief can interact with j1.

        if j2 is None: return  # done if can't interact

        derived_sentences = NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)
        # add all derived tasks to the buffer
        for derived_sentence in derived_sentences:
            self.experience_task_buffer.put(NARSDataStructures.Task(derived_sentence))
