import cProfile
import pstats
from io import StringIO

import dill as pickle
import random
import sys
import timeit
import time

import Asserts
import Config
import InputChannel
import NALInferenceRules
import NARSGUI
import NARSInferenceEngine
import NALGrammar
import NALSyntax
import NARSMemory

import NARSDataStructures.Buffers
import NARSDataStructures.Other
import NARSDataStructures.ItemContainers

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
        if Config.USE_PROFILER:
            self.pr = cProfile.Profile()
            self.pr.enable()

        self.prev_take_time = -1

        Global.Global.NARS = self # global vars are part of NARS
        self.memory = NARSMemory.Memory()
        self.global_buffer = NARSDataStructures.Buffers.Buffer(item_type=NARSDataStructures.Other.Task,
                                                               capacity=Config.GLOBAL_BUFFER_CAPACITY)
        self.vision_buffer = NARSDataStructures.Buffers.SpatialBuffer(dimensions=Config.VISION_DIMENSIONS)
        self.temporal_module = NARSDataStructures.Buffers.TemporalModule(self,item_type=NARSDataStructures.Other.Task,
                                                                         capacity=Config.EVENT_BUFFER_CAPACITY)


        self.operation_queue = [] # operations the system has queued to executed
        self.last_executed = ''
        self.current_operation_goal_sequence = None

        # enforce milliseconds per working cycle
        self.cycle_begin_time = None

        # keeps track of number of working cycles per second
        self.cycles_per_second_timer = timeit.default_timer()
        self.last_working_cycle = 0
        self.memory.conceptualize_term(Global.Global.TERM_SELF)



    def startup_and_run(self):
        self.run()


    def run(self):
        """
            Infinite loop of working cycles
        """
        while True:
            if Config.GUI_USE_INTERFACE:
                self.handle_gui_pipes()

            # global parameters
            if Global.Global.paused:
                time.sleep(0.2)
                continue

            #time.sleep(0.2)
            self.do_working_cycle()


    def do_working_cycle(self):
        """
            Performs 1 working cycle.
            In each working cycle, NARS either *Observes* OR *Considers*:
        """

        #time.sleep(0.1)
        self.memory.current_cycle_number += 1

        # debug
        if timeit.default_timer() - self.cycles_per_second_timer > 1.0:
            self.cycles_per_second_timer = timeit.default_timer()
            Global.Global.debug_print('Cycles per second: ' + str(Global.Global.get_current_cycle_number() - self.last_working_cycle))
            self.last_working_cycle = Global.Global.get_current_cycle_number()

        # track when the cycle began
        if len(self.global_buffer) > Config.GLOBAL_BUFFER_CAPACITY / 4.0: print("WARNING: GLOBAL BUFFER AT 1/4 CAPACITY "
                                                                                + str(len(self.global_buffer) / Config.GLOBAL_BUFFER_CAPACITY) + "%")

        self.cycle_begin_time = timeit.default_timer()

        # process input channel and temporal module
        InputChannel.process_input_channel()

        # OBSERVE
        #self.Observe()
        vision_sentence = self.vision_buffer.take()
        self.global_buffer.put_new(NARSDataStructures.Other.Task(vision_sentence))

        # global buffer
        buffer_len = len(self.global_buffer)
        tasks_left = buffer_len
        while tasks_left > 0:
            task_item = self.global_buffer.take()
            # process task
            self.process_task(task_item.object)
            tasks_left -= 1


        # now execute operations
        self.execute_operation_queue()

        #todo self.temporal_module.process_anticipations()

        # debug statements
        if Config.DEBUG:
            Global.Global.debug_print("operation queue: " + str(len(self.operation_queue)))
            Global.Global.debug_print("anticipations queue: " + str(len(self.temporal_module.anticipations_queue)))
            Global.Global.debug_print("global buffer: " + str(len(self.global_buffer)))

        if Config.USE_PROFILER:
            pstats.Stats(self.pr).sort_stats('tottime').print_stats(10) #tottime is time spent in the function alone, cumtime is including subfunctions
            self.pr.enable()


    def do_working_cycles(self, cycles: int):
        """
            Performs the given number of working cycles.
        """
        for i in range(cycles):
            self.do_working_cycle()


    def Observe(self):
        """
            Process a task from the global buffer.

            This function should never produce new tasks.
        """
        pass



    def Consider(self, concept=None):
        """
            Process a belief from a random concept in memory.

            This function can result in new tasks

            :param: concept: concept to consider. If None, picks a random concept
        """
        concept_item = None
        if concept is None:
            concept_item = self.memory.get_random_concept_item()
            if concept_item is None: return # nothing to ponder
            concept = concept_item.object

        # If concept is not named by a statement, get a related concept that is a statement
        attempts = 0
        max_attempts = 2
        while attempts < max_attempts \
            and not ((isinstance(concept.term, NALGrammar.Terms.StatementTerm) or
                     (isinstance(concept.term,NALGrammar.Terms.CompoundTerm) and not concept.term.is_first_order()))):
            if len(concept.term_links) > 0:
                concept = concept.term_links.peek().object
            else:
                break

            attempts += 1
        # debugs
        if Config.DEBUG:
            string = "Considering concept: " + str(concept.term)
            if concept_item is not None: string +=  str(concept_item.budget)
            if len(concept.belief_table) > 0: string += " expectation: " + str(concept.belief_table.peek().get_expectation())
            if len(concept.desire_table) > 0: string += " desirability: " + str(concept.desire_table.peek().get_desirability())
            Global.Global.debug_print(string)

        #Global.Global.debug_print("CONSIDER: " + str(concept))

        if concept is not None and attempts != max_attempts:
            #process a belief and desire
            if len(concept.belief_table) > 0:
                sentence = concept.belief_table.peek()  # get most confident belief
                self.process_judgment_sentence(sentence)

            if len(concept.desire_table) > 0:
                sentence = concept.desire_table.peek()  # get most confident goal
                self.process_goal_sentence(sentence)


        # decay priority;
        if concept_item is not None:
            self.memory.concepts_bag.decay_item(concept_item.key)



    def save_memory_to_disk(self, filename="memory1.nars"):
        """
            Save the NARS Memory instance to disk
        """
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(old_limit*2)
        with open(filename, "wb") as f:
            Global.Global.print_to_output("SAVING SYSTEM MEMORY TO FILE: " + filename)
            try:
                pickle.dump(self.memory, f, pickle.HIGHEST_PROTOCOL)
                Global.Global.print_to_output("SAVE MEMORY SUCCESS")
            except:
                Global.Global.print_to_output("SAVE MEMORY FAILURE")
        sys.setrecursionlimit(old_limit)

    def load_memory_from_disk(self, filename="memory1.nars"):
        """
            Load a NARS Memory instance from disk.
            This will override the NARS' current memory
        """
        try:
            with open(filename, "rb") as f:
                Global.Global.print_to_output("LOADING SYSTEM MEMORY FILE: " + filename)
                # load memory from file
                self.memory = pickle.load(f)
                # Print memory contents to internal data GUI
                if Config.GUI_USE_INTERFACE:
                    Global.Global.clear_output_gui(data_structure=self.memory.concepts_bag)
                    for item in self.memory.concepts_bag:
                        if item not in self.memory.concepts_bag:
                            Global.Global.print_to_output(msg=str(item), data_structure=self.memory.concepts_bag)

                if Config.GUI_USE_INTERFACE:
                    NARSGUI.NARSGUI.gui_total_cycles_stringvar.set("Cycle #" + str(self.memory.current_cycle_number))

                Global.Global.print_to_output("LOAD MEMORY SUCCESS")
        except:
            Global.Global.print_to_output("LOAD MEMORY FAIL")

    def handle_gui_pipes(self):
        if Global.Global.NARS_object_pipe is None: return

        # GUI
        Global.Global.NARS_string_pipe.send(("cycles", "Cycle #" + str(self.memory.current_cycle_number), None, 0))


        while Global.Global.NARS_object_pipe.poll():
            # for blocking communication only, when the sender expects a result.
            # This checks for a message request from the GUI
            (command, key, data_structure_id) = Global.Global.NARS_object_pipe.recv()
            if command == "getitem":
                data_structure = None
                if data_structure_id == str(self.temporal_module):
                    data_structure = self.temporal_module
                elif data_structure_id == str(self.memory.concepts_bag):
                    data_structure = self.memory.concepts_bag
                if data_structure is not None:
                    item = None
                    while item is None:
                        item: NARSDataStructures.ItemContainers.Item = data_structure.peek_from_item_archive(key)
                    Global.Global.NARS_object_pipe.send(item.get_gui_info())
            elif command == "getsentence":
                sentence_string = key
                statement_start_idx = sentence_string.find(NALSyntax.StatementSyntax.Start.value)
                statement_end_idx = sentence_string.rfind(NALSyntax.StatementSyntax.End.value)
                statement_string = sentence_string[statement_start_idx:statement_end_idx+1]
                term = NALGrammar.Terms.string_to_term_dict[statement_string]
                concept_item = self.memory.peek_concept_item(term)
                concept = concept_item.object

                if concept is None:
                    Global.Global.NARS_object_pipe.send(None)  # couldn't get concept, maybe it was purged
                else:
                    punctuation_str = sentence_string[statement_end_idx + 1]
                    if punctuation_str == NALSyntax.Punctuation.Judgment.value:
                        table = concept.belief_table
                    elif punctuation_str == NALSyntax.Punctuation.Goal.value:
                        table = concept.desire_table
                    else:
                        assert False,"ERROR: Could not parse GUI sentence fetch"
                    ID = sentence_string[sentence_string.find(Global.Global.MARKER_ITEM_ID) + len(
                        Global.Global.MARKER_ITEM_ID):sentence_string.rfind(Global.Global.MARKER_ID_END)]
                    sent = False
                    for knowledge_tuple in table:
                        knowledge_sentence = knowledge_tuple[0]
                        knowledge_sentence_str = str(knowledge_sentence)
                        knowledge_sentence_ID = knowledge_sentence_str[knowledge_sentence_str.find(Global.Global.MARKER_ITEM_ID) + len(
                            Global.Global.MARKER_ITEM_ID):knowledge_sentence_str.rfind(Global.Global.MARKER_ID_END)]
                        if ID == knowledge_sentence_ID:
                            Global.Global.NARS_object_pipe.send(("sentence",knowledge_sentence.get_gui_info()))
                            sent = True
                            break
                    if not sent: Global.Global.NARS_object_pipe.send(("concept",concept_item.get_gui_info())) # couldn't get sentence, maybe it was purged
            elif command == "getconcept":
                item = self.memory.peek_concept_item(key)
                if item is not None:
                    Global.Global.NARS_object_pipe.send(item.get_gui_info())
                else:
                    Global.Global.NARS_object_pipe.send(None)  # couldn't get concept, maybe it was purged

        while Global.Global.NARS_string_pipe.poll():
            # this pipe can hold as many tasks as needed
            (command, data) = Global.Global.NARS_string_pipe.recv()


            if command == "userinput":
                InputChannel.parse_and_queue_input_string(data)
            elif command == "visualimage":
                # user loaded image for visual input
                img = data
                InputChannel.queue_visual_sensory_image_array(img)
            elif command == "visualimagelabel":
                # user loaded image for visual input
                label = data
                InputChannel.parse_and_queue_input_string("(" + label + "--> SEEN). :|:")
            elif command == "duration":
                Config.TAU_WORKING_CYCLE_DURATION = data
            elif command == "paused":
                Global.Global.paused = data


    def process_task(self, task: NARSDataStructures.Other.Task):
        """
            Processes any Narsese task
        """
        Asserts.assert_task(task)

        j = task.sentence
        task_statement_term = j.statement
        if task_statement_term.contains_variable(): return  # todo handle variables

        # statement_concept_item = self.memory.peek_concept_item(task_statement_term)
        # statement_concept = statement_concept_item.object


        # get (or create if necessary) statement concept, and sub-term concepts recursively
        if isinstance(j, NALGrammar.Sentences.Judgment):
            self.process_judgment_task(task)
        elif isinstance(j, NALGrammar.Sentences.Question):
            self.process_question_task(task)
        elif isinstance(j, NALGrammar.Sentences.Goal):
            self.process_goal_task(task)

        #     if not task.sentence.is_event():
        #         statement_concept_item.budget.set_quality(0.99)
        #         self.memory.concepts_bag.change_priority(key=statement_concept_item.key,
        #                                                  new_priority=0.99)
        #
        # self.memory.concepts_bag.strengthen_item(key=statement_concept_item.key)
        #print("concept strengthen " + str(statement_concept_item.key) + " to " + str(statement_concept_item.budget))


    def process_judgment_task(self, task: NARSDataStructures.Other.Task):
        """
            Processes a Narsese Judgment Task
            Insert it into the belief table and revise it with another belief

            :param Judgment Task to process
        """
        Asserts.assert_task(task)

        j = task.sentence
        if j.is_event() and j.stamp.derived_by is None:
            # only put non-derived atomic events in temporal module for now
            Global.Global.NARS.temporal_module.put_new(task)

        if isinstance(j.statement, NALGrammar.Terms.CompoundTerm)\
            and j.statement.connector == NALSyntax.TermConnector.Negation:
            j = NALInferenceRules.Immediate.Negation(j)

        task_statement_concept = self.memory.peek_concept(j.statement)

        # todo commented out immediate inference because it floods the system
        # derived_sentences = []#NARSInferenceEngine.do_inference_one_premise(j)
        # for derived_sentence in derived_sentences:
        #    self.global_buffer.put_new(NARSDataStructures.Other.Task(derived_sentence))

        # if j.is_event():
        #     # anticipate event j
        #     pass #todo self.temporal_module.anticipate_from_event(j)

        task_statement_concept.belief_table.put(j)

        current_belief = task_statement_concept.belief_table.peek()
        self.process_judgment_sentence(current_belief)

        if Config.DEBUG:
            string = "Integrated new BELIEF Task: " + j.get_formatted_string() + "from "
            for premise in j.stamp.parent_premises:
                string += str(premise) + ","
            Global.Global.debug_print(string)


    def process_judgment_sentence(self, j1: NALGrammar.Sentences.Judgment, revise=True):
        """
            Continued processing for Judgment

            :param j1: Judgment
            :param related_concept: concept related to judgment with which to perform semantic inference
        """
        if Config.DEBUG:
            Global.Global.debug_print("Continued Processing JUDGMENT: " + str(j1))

        # get terms from sentence
        statement_term = j1.statement

        # do regular semantic inference
        results = self.process_sentence_semantic_inference(j1)
        for result in results:
            self.global_buffer.put_new(NARSDataStructures.Other.Task(result))


    def process_question_task(self, task):
        """
            Process a Narsese question task

            Get the best answer to the question if it's known and perform inference with it;
            otherwise, use backward inference to derive new questions that could lead to an answer.

            #todo handle variables
            #todo handle tenses
        """
        Asserts.assert_task(task)

        # get the best answer from concept belief table
        best_answer: NALGrammar.Sentences.Judgment = task_statement_concept.belief_table.peek_max()
        j1 = None
        if best_answer is not None:
            #
            # Answer the question
            #
            if task.is_from_input and task.needs_to_be_answered_in_output:
                Global.Global.print_to_output("OUT: " + best_answer.get_formatted_string())
                task.needs_to_be_answered_in_output = False

            # do inference between answer and a related belief
            j1 = best_answer
        else:
            # do inference between question and a related belief
            j1 = task.sentence

        self.process_sentence_semantic_inference(j1)


    def process_goal_task(self, task: NARSDataStructures.Other.Task):
        """
            Processes a Narsese Goal Task

            :param Goal Task to process
        """
        Asserts.assert_task(task)

        j = task.sentence

        """
            Initial Processing

            Insert it into the desire table or revise with the most confident desire
        """
        task_statement_concept = self.memory.peek_concept(j.statement)

        # store the most confident desire
        task_statement_concept.desire_table.put(j)

        current_desire = task_statement_concept.desire_table.peek()

        self.process_goal_sentence(current_desire)

        if Config.DEBUG:
            string = "Integrated new GOAL Task: " + j.get_formatted_string() + "from "
            for premise in j.stamp.parent_premises:
                string += str(premise) + ","
            Global.Global.debug_print(string)


    def process_goal_sentence(self, j: NALGrammar.Sentences.Goal):
        """
            Continued processing for Goal

            :param j: Goal
            :param related_concept: concept related to goal with which to perform semantic inference
        """
        if Config.DEBUG: Global.Global.debug_print("Continued Processing GOAL: " + str(j))

        statement = j.statement

        statement_concept: NARSMemory.Concept = self.memory.peek_concept(statement)

        # see if it should be pursued
        should_pursue = NALInferenceRules.Local.Decision(j)
        if not should_pursue:
            #Global.Global.debug_print("Goal failed decision-making rule " + j.get_formatted_string())
            if Config.DEBUG and statement.is_op():
                Global.Global.debug_print("Operation failed decision-making rule " + j.get_formatted_string())
            return  # Failed decision-making rule
        else:
            pass#Global.Global.debug_print("Goal passed decision-making rule " + j.get_formatted_string())


        # at this point the system wants to pursue this goal.
        # now check if it should be inhibited (negation is more highly desired).
        # negated_statement = j.statement.get_negated_term()
        # negated_concept = self.memory.peek_concept(negated_statement)
        # if len(negated_concept.desire_table) > 0:
        #     desire = j.get_expectation()
        #     neg_desire = negated_concept.desire_table.peek().get_expectation()
        #     should_inhibit = neg_desire > desire
        #     if should_inhibit:
        #         Global.Global.debug_print("Event was inhibited " + j.get_term_string())
        #         return  # Failed inhibition decision-making rule
        if statement.is_op() and not j.statement.connector == NALSyntax.TermConnector.Negation:
            #if not j.executed:
            self.queue_operation(j)
            #    j.executed = False
        else:
            # check if goal already achieved
            desire_event = statement_concept.belief_table.peek()
            if desire_event is not None:
                if desire_event.is_positive():
                    Global.Global.debug_print(str(desire_event) + " is positive for goal: " + str(j))
                    return  # Return if goal is already achieved

            if isinstance(statement, NALGrammar.Terms.CompoundTerm):
                if NALSyntax.TermConnector.is_conjunction(statement.connector):
                    # if it's a conjunction (A &/ B), simplify using true beliefs (e.g. A)
                    subterm = statement.subterms[0]
                    subterm_concept = Global.Global.NARS.memory.peek_concept(subterm)
                    belief = subterm_concept.belief_table.peek()
                    if belief is not None and belief.is_positive():
                        # the first component of the goal is positive, do inference and derive the remaining goal component
                        results = NARSInferenceEngine.do_semantic_inference_two_premise(j, belief)
                        for result in results:
                            self.global_buffer.put_new(NARSDataStructures.Other.Task(result))
                        return # done deriving goals
                    else:
                        if Config.DEBUG: Global.Global.debug_print(str(subterm_concept.term) + " was not positive to split conjunction.")
                elif statement.connector == NALSyntax.TermConnector.Negation\
                and NALSyntax.TermConnector.is_conjunction(statement.subterms[0].connector):
                    # if it's a negated conjunction (--,(A &/ B))!, simplify using true beliefs (e.g. A.)
                    # (--,(A &/ B)) ==> D and A
                    # induction
                    # :- (--,(A &/ B)) && A ==> D :- (--,B) ==> D :- (--,B)!
                    conjunction = statement.subterms[0]
                    subterm = conjunction.subterms[0]
                    subterm_concept = Global.Global.NARS.memory.peek_concept(subterm)
                    belief = subterm_concept.belief_table.peek()
                    if belief is not None and belief.is_positive():
                        # the first component of the goal is negative, do inference and derive the remaining goal component
                        results = NARSInferenceEngine.do_semantic_inference_two_premise(j, belief)
                        for result in results:
                            self.global_buffer.put_new(NARSDataStructures.Other.Task(result))

                        return # done deriving goals

            # random_belief = None
            # contextual_belief = None
            # if len(statement_concept.explanation_links) > 0 and j.statement.connector != NALSyntax.TermConnector.Negation:
            #     # process with random and context-relevant explanation A =/> B
            #     random_belief = self.memory.get_random_bag_explanation(j) # (E =/> G)
            #     #contextual_belief = self.memory.get_best_explanation_with_true_precondition(j)
            # elif len(statement_concept.prediction_links) > 0 and j.statement.connector == NALSyntax.TermConnector.Negation:
            #     random_belief = self.memory.get_random_bag_prediction(j) # ((--,G) =/> E)
            #     #contextual_belief = self.memory.get_prediction_preferred_with_true_postcondition(j) # ((--,G) =/> E)
            #
            # if random_belief is not None:
            #      if Config.DEBUG:Global.Global.debug_print(str(random_belief) + " is random explanation for " + str(j))
            #      # process goal with explanation
            #      results = NARSInferenceEngine.do_semantic_inference_two_premise(j, random_belief)
            #      for result in results:
            #          self.global_buffer.put_new(NARSDataStructures.Other.Task(result))
            #
            #      self.process_judgment_sentence(random_belief)
            #
            #
            # if contextual_belief is not None:
            #     if Config.DEBUG: Global.Global.debug_print(str(contextual_belief) + " is contextual explanation for " + str(j))
            #     # process goal with explanation
            #     results = NARSInferenceEngine.do_semantic_inference_two_premise(j, contextual_belief)
            #     for result in results:
            #         self.global_buffer.put_new(NARSDataStructures.Other.Task(result))
            #
            #     self.process_judgment_sentence(contextual_belief)
            #
            # else:
            #     if Config.DEBUG: Global.Global.debug_print("No contextual explanations for " + str(j))


    def process_sentence_semantic_inference(self, j1, related_concept=None):
        """
            Processes a Sentence with a belief from a related concept.

            :param j1 - sentence to process
            :param related_concept - (Optional) concept from which to fetch a belief to process the sentence with

            #todo handle variables
        """
        results = []
        if Config.DEBUG: Global.Global.debug_print("Processing: " + j1.get_formatted_string())
        statement_term = j1.statement
        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        if related_concept is None:
            if Config.DEBUG: Global.Global.debug_print("Processing: Peeking randomly related concept")
            if isinstance(statement_term, NALGrammar.Terms.SpatialTerm):
                if len(statement_concept.prediction_links) > 0:
                    related_concept = statement_concept.prediction_links.peek().object
            elif isinstance(statement_term, NALGrammar.Terms.StatementTerm) \
                    and not statement_term.is_first_order():
                    subject_term = statement_term.get_subject_term()
                    related_concept = self.memory.peek_concept(subject_term)
            elif isinstance(statement_term, NALGrammar.Terms.StatementTerm) \
                    and statement_term.is_first_order() \
                    and j1.is_event():
                if len(statement_concept.explanation_links) > 0:
                    related_concept = statement_concept.explanation_links.peek().object
                elif len(statement_concept.superterm_links) > 0:
                    related_concept = statement_concept.superterm_links.peek().object
            else:
                related_concept = self.memory.get_semantically_related_concept(statement_concept)

            if related_concept is None: self.memory.get_semantically_related_concept(statement_concept)
            if related_concept is None: return []
        else:
            Global.Global.debug_print("Processing: Using related concept " + str(related_concept))

        # check for a belief we can interact with
        j2 = related_concept.belief_table.peek_random()

        if j2 is None:
            if Config.DEBUG: Global.Global.debug_print('No related beliefs found for ' + j1.get_formatted_string())
            return results  # done if can't interact

        results = NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)

        # check for a belief we can interact with
        j2 = related_concept.desire_table.peek_random()

        if j2 is None:
            if Config.DEBUG: Global.Global.debug_print('No related goals found for ' + j1.get_formatted_string())
            return results # done if can't interact

        results += NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)

        return results

    """
        OPERATIONS
    """

    def queue_operation(self, operation_goal):
        """
            Queue a desired operation.
            Can be an atomic operation or a compound.
        :param operation_goal: Including SELF, arguments, and Operation itself
        :return:
        """
        # todo extract and use args
        if Config.DEBUG:
            Global.Global.debug_print("Attempting queue operation: " + str(operation_goal))
        # full_operation_term.get_subject_term()
        operation_statement = operation_goal.statement
        desirability = operation_goal.get_desirability()

        if self.current_operation_goal_sequence is not None:
            # in the middle of a operation sequence already
            better_goal = NALInferenceRules.Local.Choice(operation_goal, self.current_operation_goal_sequence)
            if better_goal is self.current_operation_goal_sequence: return # don't execute since the current sequence is more desirable
            # else, the given operation is more desirable
            self.operation_queue.clear()

        if Config.DEBUG: Global.Global.debug_print("Queueing operation: " + str(operation_goal))

        parent_strings = []
        # create an anticipation if this goal was based on a higher-order implication
        for parent in operation_goal.stamp.parent_premises:
            parent_strings.append(str(parent))

        # insert operation into queue to be execute after the interval
        # intervals of zero will result in immediate execution (assuming the queue is processed afterwards and in the same cycle as this function)
        if isinstance(operation_statement,NALGrammar.Terms.StatementTerm):
            # atomic op
            self.current_operation_goal_sequence = operation_goal
            self.operation_queue.append([0, operation_statement, desirability, parent_strings])
        elif isinstance(operation_statement,NALGrammar.Terms.CompoundTerm):
            # higher-order operation like A &/ B or A &| B
            atomic_ops_left_to_execute = len(operation_statement.subterms)
            self.current_operation_goal_sequence = operation_goal

            working_cycles = 0
            for i in range(len(operation_statement.subterms)):
                # insert the atomic subterm operations and their working cycle delays
                subterm = operation_statement.subterms[i]
                self.operation_queue.append([working_cycles, subterm, desirability, parent_strings])
                if i < len(operation_statement.subterms)-1:
                    working_cycles += NALInferenceRules.HelperFunctions.convert_from_interval(operation_statement.intervals[i])

        if Config.DEBUG: Global.Global.debug_print("Queued operation: " + str(operation_statement))


    def execute_operation_queue(self):
        """
            Loop through all operations and decrement their remaining interval delay.
            If delay is zero, execute the operation
        :return:
        """
        self.last_executed = None
        i = 0
        while i < len(self.operation_queue):
            remaining_working_cycles, operation_statement, desirability, parents = self.operation_queue[i]

            if remaining_working_cycles == 0:
                # operation is ready to execute
                self.execute_atomic_operation(operation_statement, desirability, parents)
                # now remove it from the queue
                self.operation_queue.pop(i)
                self.last_executed = operation_statement
                i -= 1
            else:
                # decrease remaining working cycles
                self.operation_queue[i][0] -= 1
            i += 1

        if len(self.operation_queue) == 0: self.current_operation_goal_sequence = None


    def execute_atomic_operation(self, operation_statement_to_execute, desirability, parents):
        statement_concept: NARSMemory.Concept = self.memory.peek_concept(operation_statement_to_execute)

        # execute an atomic operation immediately
        predicate_str = str(operation_statement_to_execute.get_predicate_term())
        current_cycle = str(Global.Global.get_current_cycle_number())
        string = "EXE: ^" + predicate_str +\
        " cycle #" + current_cycle +\
        " based on desirability: " + str(desirability) +\
        " and parents: " + str(parents)

        Global.Global.print_to_output(string)


        # input the operation statement
        operation_event = NALGrammar.Sentences.Judgment(operation_statement_to_execute,
                                                        NALGrammar.Values.TruthValue(),
                                                        occurrence_time=Global.Global.get_current_cycle_number())
        InputChannel.process_sentence_into_task(operation_event)

