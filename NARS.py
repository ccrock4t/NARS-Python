import pickle
import random
import time

import Config
import InputChannel
import NALInferenceRules
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
        self.event_buffer = NARSDataStructures.EventBuffer(item_type=NARSDataStructures.Task, capacity=10)
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
                    NARSGUI.NARSGUI.gui_total_cycles_stringvar.set("Cycle #" + str(self.memory.current_cycle_number))

                NARSGUI.NARSGUI.print_to_output("LOAD MEMORY SUCCESS")
        except:
            NARSGUI.NARSGUI.print_to_output("LOAD MEMORY FAIL")

    def run(self):
        """
            Infinite loop of working cycles
        """
        while True:
            # global parameters
            if Global.Global.paused:
                time.sleep(0.2)
                continue

            if self.delay > 0:
                time.sleep(self.delay)

            self.do_working_cycle()

    def do_working_cycle(self):
        """
            Performs 1 working cycle.
            In each working cycle, NARS either *Observes* OR *Considers*:
        """
        if Global.Global.gui_use_interface:
            NARSGUI.NARSGUI.gui_total_cycles_stringvar.set("Cycle #" + str(self.memory.current_cycle_number))

        InputChannel.process_next_pending_sentence() # process strings coming from input buffer

        self.Process_Event_Buffer() # process events from the event buffer

        # now do something with tasks from experience buffer and/or knowledge from memory
        for _ in range(3):
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

    def Process_Event_Buffer(self):
        """
            Process events into the experience buffer
        """
        if len(self.event_buffer) > 1: # need multiple events to process implications
            event_task_A = self.event_buffer.take().object # take an event from the buffer
            event_A = event_task_A.sentence

            event_task_B = self.event_buffer.take().object # take another event from the buffer
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

        if isinstance(task_item.object.sentence, NALGrammar.Question):
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

        if isinstance(concept_item.object.term, NALGrammar.StatementTerm):
            # Concept is S --> P or S ==> P
            concept_to_consider = concept_item.object
        else:
            # Concept is S or P
            concept_to_consider = self.memory.get_semantically_related_concept(concept_item.object)

        if concept_to_consider is not None:
            rand_int = random.randint(1,2) # 1 for belief, 2 for desire
            if rand_int == 1 or len(concept_to_consider.desire_table) == 0:
                if len(concept_to_consider.belief_table) > 0:
                    sentence = concept_to_consider.belief_table.peek() # get most confident belief
                    self.process_judgment_sentence(sentence)
            elif rand_int == 2 or len(concept_to_consider.belief_table) == 0:
                if len(concept_to_consider.desire_table) > 0:
                    sentence = concept_to_consider.desire_table.peek() # get most confident belief
                    self.process_goal_sentence(sentence)

         # decay priority
        concept_item = self.memory.concepts_bag.take_using_key(concept_item.key)
        concept_item.decay()
        self.memory.concepts_bag.put(concept_item)

    def process_task(self, task: NARSDataStructures.Task):
        """
            Processes any Narsese task
        """
        NARSDataStructures.assert_task(task)

        if isinstance(task.sentence, NALGrammar.Judgment):
            self.process_judgment_task(task)
        elif isinstance(task.sentence, NALGrammar.Question) \
                or NALGrammar.VariableTerm.QUERY_SYM in str(task.sentence.statement):
            self.process_question_task(task)
        elif isinstance(task.sentence, NALGrammar.Goal):
            self.process_goal_task(task)

    def process_judgment_task(self, task: NARSDataStructures.Task):
        """
            Processes a Narsese Judgment Task

            :param Judgment Task to process
        """
        NARSDataStructures.assert_task(task)

        j1 = task.sentence

        # get terms from sentence
        statement_term = j1.statement

        if statement_term.contains_variable(): return #todo handle variables

        """
            Initial Processing
            
            Revise this judgment with the most confident belief, then insert it into the belief table
        """
        #derived_sentences = NARSInferenceEngine.do_inference_one_premise(j1)
        #for derived_sentence in derived_sentences:
        #    self.experience_task_buffer.put(NARSDataStructures.Task(derived_sentence))

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        # add the judgment itself into concept's belief table
        statement_concept.belief_table.put(j1)

        """
            Continued processing
        
            Do local/forward inference on a related belief
        """
        # revise the judgment
        self.process_judgment_sentence(j1, statement_concept)

    def process_judgment_sentence(self, j1: NALGrammar.Goal, related_concept=None):
        """
            Continued processing for Judgment

            :param j1: Judgment
            :param related_concept: concept related to judgment with which to perform semantic inference
        """
        self.process_sentence_semantic_inference(j1, related_concept)

    def process_question_task(self, task):
        """
            Process a Narsese question task

            Get the best answer to the question if it's known and perform inference with it;
            otherwise, use backward inference to derive new questions that could lead to an answer.

            #todo handle variables
            #todo handle tenses
        """
        NARSDataStructures.assert_task(task)

        # get terms from sentence
        statement_term = task.sentence.statement

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

        self.process_sentence_semantic_inference(j1)

    def process_goal_task(self, task: NARSDataStructures.Task):
        """
            Processes a Narsese Goal Task

            :param Goal Task to process
        """
        NARSDataStructures.assert_task(task)

        j1 = task.sentence

        # get terms from sentence
        statement_term = j1.statement

        if statement_term.contains_variable(): return  # todo handle variables

        """
            Initial Processing

            Insert it into the desire table and revise with the most confident desire
        """
        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        # add the judgment itself into concept's desire table
        statement_concept.desire_table.put(j1)

        """
            Continued processing
        """
        self.process_goal_sentence(j1, statement_concept)

    def process_goal_sentence(self, j1: NALGrammar.Goal, related_concept=None):
        """
            Continued processing for Goal

            :param j1: Goal
            :param related_concept: concept related to goal with which to perform semantic inference
        """
        should_pursue = NALInferenceRules.Local.Decision(j1.value.frequency, j1.value.confidence)
        if not should_pursue: return # Failed decision-making rule

        statement_term = j1.statement

        statement_concept = self.memory.peek_concept(statement_term)
        belief = statement_concept.belief_table.peek()
        if belief is not None and belief.is_positive(): return # Goal is already achieved

        if statement_term.is_operation():
            self.execute_operation(j1.statement)

        self.process_sentence_semantic_inference(j1, related_concept=related_concept)


    def process_sentence_semantic_inference(self, j1, related_concept=None):
        """
            Processes a Sentence with a belief from a related concept.

            :param j1 - sentence to process
            :param related_concept - (Optional) concept to process the sentence with

            #todo handle variables
            #todo handle tenses
        """
        if Global.Global.DEBUG: print("Processing: " + j1.get_formatted_string())
        statement_term = j1.statement
        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        if statement_term.contains_variable(): return
        j2 = None
        if related_concept is None:
            number_of_attempts = 0
            while j2 is None and number_of_attempts < Config.NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_BELIEF: # try searching a maximum of 3 concepts
                related_concept = self.memory.get_semantically_related_concept(statement_concept)
                if related_concept is None:
                    if Global.Global.DEBUG: print("No related concepts?")
                    return  # no related concepts! Should never happen, the concept is always semantically related to itself

                # check for a belief we can interact with

                for (belief, confidence) in related_concept.belief_table:
                    if NALGrammar.Sentence.may_interact(j1,belief):
                        j2 = belief # belief can interact with j1
                        break

                number_of_attempts += 1
        else:
            for (belief, confidence) in related_concept.belief_table:
                if NALGrammar.Sentence.may_interact(j1, belief):
                    j2 = belief  # belief can interact with j1
                    break

        if j2 is None:
            if Global.Global.DEBUG: print('No related belief for ' + j1.get_formatted_string())
            return  # done if can't interact

        if Global.Global.DEBUG: print("Trying inference between: " + j1.get_formatted_string() + " and " + j2.get_formatted_string())
        derived_sentences = NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)
        for derived_sentence in derived_sentences:
            self.experience_task_buffer.put(NARSDataStructures.Task(derived_sentence))

    def execute_operation(self, full_operation_statement):
        """

        :param full_operation_statement: Including SELF, arguments, and Operation itself
        :return:
        """
        #todo extract and use args
        # full_operation_term.get_subject_term()
        operation = full_operation_statement.get_predicate_term()
        NARSGUI.NARSGUI.print_to_output("EXE: ^" + str(operation))
        operation_event = NALGrammar.Judgment(full_operation_statement, NALGrammar.TruthValue(), occurrence_time=Global.Global.get_current_cycle_number())
        self.event_buffer.put(NARSDataStructures.Task(operation_event))
