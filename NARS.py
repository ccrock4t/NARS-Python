import pickle
import random
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
        self.global_buffer = NARSDataStructures.Buffers.Buffer(item_type=NARSDataStructures.Other.Task,
                                                               capacity=Config.GLOBAL_BUFFER_CAPACITY)
        self.temporal_module = NARSDataStructures.Buffers.TemporalModule(self,item_type=NARSDataStructures.Other.Task, capacity=Config.EVENT_BUFFER_CAPACITY)
        self.memory = NARSMemory.Memory()

        self.operation_queue = [] # operations the system has queued to executed
        self.current_operation_sequence = None

        # enforce configurable milliseconds per working cycle
        self.cycle_begin_time = None

        # keeps track of number of working cycles per second
        self.cycles_per_second_timer = time.time()
        self.last_working_cycle = 0


    def run(self):
        """
            Infinite loop of working cycles
        """
        while True:
            if Config.GUI_USE_INTERFACE: self.handle_gui_pipes()
            # global parameters
            if Global.Global.paused:
                time.sleep(0.2)
                continue

            self.do_working_cycle()

    def do_working_cycle(self):
        """
            Performs 1 working cycle.
            In each working cycle, NARS either *Observes* OR *Considers*:
        """
        # track when the cycle began
        self.cycle_begin_time = time.time()

        # debug
        if time.time() - self.cycles_per_second_timer > 1.0:
            self.cycles_per_second_timer = time.time()
            print('Cycles per second: ' + str(Global.Global.get_current_cycle_number() - self.last_working_cycle))
            self.last_working_cycle = Global.Global.get_current_cycle_number()

        # GUI
        if Config.GUI_USE_INTERFACE: Global.Global.NARS_string_pipe.send(("cycles", "Cycle #" + str(self.memory.current_cycle_number), None, 0))

        # do stuff with buffer and memory while there is time
        while (time.time() - self.cycle_begin_time) * 1000 < Config.TAU_WORKING_CYCLE_DURATION:
            if InputChannel.input_queue.qsize() > 0:
                # process input channel and temporal module
                if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
                InputChannel.process_pending_sentence()
                if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
                    "Process input sentence took " + str((time.time() - before) * 1000) + "ms")
                if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
                self.process_temporal_chaining()  # process events from the event buffer
                if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print("Chaining took " + str((time.time() - before) * 1000) + "ms")

            rand = random.random()
            if rand < Config.MINDFULNESS and len(self.global_buffer) > 0:
                # OBSERVE
                if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
                self.Observe()
                if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print("Observe took " + str((time.time() - before)*1000) + "ms")
            else:
                # CONSIDER
                if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
                self.Consider()
                if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print("Consider took " + str((time.time() - before) * 1000) + "ms")

        # now execute operations
        if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
        self.execute_operation_queue()
        if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print("Execute Operations Queue took " + str((time.time() - before) * 1000) + "ms")

        if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
        self.temporal_module.process_anticipations()
        if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
            "Anticipations Queue took " + str((time.time() - before) * 1000) + "ms")

        # debug statements
        if Config.DEBUG:
            Global.Global.debug_print("global buffer: " + str(len(self.global_buffer)))

        if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print('Cycle took: ' + str((time.time() - self.cycle_begin_time)*1000) + "ms")

        # if using GUI, sleep 4 ms, otherwise GUI doesn't work
        if Config.GUI_USE_INTERFACE: time.sleep(0.005)

        # done
        self.memory.current_cycle_number += 1

    def do_working_cycles(self, cycles: int):
        """
            Performs the given number of working cycles.
        """
        for i in range(cycles):
            self.do_working_cycle()

    def process_temporal_chaining(self):
        """
            Process temporal chaining
        """
        if len(self.temporal_module) > 0:
            self.temporal_module.temporal_chaining_3()


    def Observe(self):
        """
            Process a task from the global buffer.

            This function should never produce new tasks.
        """
        if len(self.global_buffer) > 0:
            if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
            task_item = self.global_buffer.take()
            if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
                "Take from global buffer took " + str((time.time() - before) * 1000) + "ms")

            if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
            # process task
            self.process_task(task_item.object)
            if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
                "Process task took " + str((time.time() - before) * 1000) + "ms")

    def Consider(self):
        """
            Process a random concept in memory.

            This function can result in new tasks

            :param: concept: concept to consider. If None, picks a random concept
        """
        concept_item = self.memory.get_random_concept_item()
        if concept_item is None: return # nothing to ponder
        concept = concept_item.object

        original_concept_item = concept_item

        attempts = 0
        max_attempts = 2
        while attempts < max_attempts \
            and not (isinstance(concept.term, NALGrammar.Terms.StatementTerm) or (isinstance(concept.term,NALGrammar.Terms.CompoundTerm) and not concept.term.is_first_order())):
            # Concept is not named by a statement, get a related statement concept
            if len(concept.term_links) > 0:
                concept = concept.term_links.peek().object
            else:
                break

            attempts += 1

        if Config.DEBUG:
            string = "Considering concept: " + str(concept.term)
            if concept_item is not None: string += " $" + str(concept_item.budget.get_priority()) + "$"
            if len(concept.belief_table) > 0: string += " expectation: " + str(concept.belief_table.peek().get_expectation())
            if len(concept.desire_table) > 0: string += " desirability: " + str(concept.desire_table.peek().get_desirability())
            Global.Global.debug_print(string)

        if concept is not None and attempts != max_attempts:
            #process a belief and desire

            if len(concept.desire_table) > 0:
                sentence = concept.desire_table.peek()  # get most confident goal
                self.process_goal_sentence(sentence)

            if len(concept.belief_table) > 0:
                sentence = concept.belief_table.peek()  # get most confident belief
                self.process_judgment_sentence(sentence)

            if len(concept.belief_table) > 0:
                s = concept.belief_table.peek()
                if Config.DEBUG and s.is_event() and isinstance(s.statement, NALGrammar.Terms.StatementTerm):
                    print("Is " + str(s.statement) + " positive? " + str(s.is_positive()))

        # decay priority; take concept out of bag and replace
        if concept_item is not None:
            self.memory.concepts_bag.decay_item(concept_item.key)

        if attempts > 1:
            # decay priority; take concept out of bag and replace
            self.memory.concepts_bag.decay_item(original_concept_item.key)

    def save_memory_to_disk(self, filename="memory1.narsmemory"):
        """
            Save the NARS Memory instance to disk
        """
        with open(filename, "wb") as f:
            Global.Global.print_to_output("SAVING SYSTEM MEMORY TO FILE: " + filename)
            pickle.dump(self.memory, f, pickle.HIGHEST_PROTOCOL)
            Global.Global.print_to_output("SAVE MEMORY SUCCESS")

    def load_memory_from_disk(self, filename="memory1.narsmemory"):
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
        while Global.Global.NARS_object_pipe.poll():
            # for blocking communication only, when the sender expects a result.
            # check for message request from GUI
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
                statement_term = NALGrammar.Terms.Term.from_string(statement_string)
                concept_item = self.memory.peek_concept_item(statement_term)
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
            (command, key) = Global.Global.NARS_string_pipe.recv()

            if command == "userinput":
                if InputChannel.is_sensory_input_string(key):
                    # don't split by lines, this is an array input
                    InputChannel.add_input_string(key)
                else:
                    # treat each line as a separate input
                    lines = key.splitlines(False)
                    for line in lines:
                        InputChannel.add_input_string(line)
            elif command == "duration":
                Config.TAU_WORKING_CYCLE_DURATION = key
            elif command == "paused":
                Global.Global.paused = key


    def process_task(self, task: NARSDataStructures.Other.Task):
        """
            Processes any Narsese task
        """
        Asserts.assert_task(task)

        sentence = task.sentence
        task_statement_term = sentence.statement
        if task_statement_term.contains_variable(): return  # todo handle variables

        if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept_item = self.memory.peek_concept_item(task_statement_term)
        statement_concept = statement_concept_item.object
        if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
            "Get concept item took " + str((time.time() - before) * 1000) + "ms")

        if isinstance(task.sentence, NALGrammar.Sentences.Judgment):
            self.process_judgment_task(task,statement_concept)
        elif isinstance(task.sentence, NALGrammar.Sentences.Question):
            self.process_question_task(task,statement_concept)
        elif isinstance(task.sentence, NALGrammar.Sentences.Goal):
            self.process_goal_task(task,statement_concept)

        if task.sentence.is_event():
            # increase priority; take concept out of bag and replace
            self.memory.concepts_bag.strengthen_item(statement_concept_item.key)

    def process_judgment_task(self, task: NARSDataStructures.Other.Task, task_statement_concept):
        """
            Processes a Narsese Judgment Task
            Insert it into the belief table and revise it with another belief

            :param Judgment Task to process
        """
        Asserts.assert_task(task)

        j = task.sentence

        # commented out because it floods the system
        #derived_sentences = NARSInferenceEngine.do_inference_one_premise(j1)
        #for derived_sentence in derived_sentences:
        #   self.global_task_buffer.put_new(NARSDataStructures.Other.Task(derived_sentence))

        current_belief = task_statement_concept.belief_table.peek()

        best_belief = None
        if NALGrammar.Sentences.may_interact(j,current_belief):
            # do a Revision
            revised = NARSInferenceEngine.do_semantic_inference_two_premise(j, current_belief)[0]
            self.global_buffer.put_new(NARSDataStructures.Other.Task(revised))
        else:
            if j.is_event():
                if current_belief is not None:
                    best_belief = NALInferenceRules.Local.Choice(j,current_belief,only_confidence=True)
                    # only keep one event
                    task_statement_concept.belief_table.take()
                    task_statement_concept.belief_table.put(best_belief)
                else:
                    task_statement_concept.belief_table.put(j)

                # anticipate event j
                self.temporal_module.anticipate_from_event(j)
            else:
                task_statement_concept.belief_table.put(j)


        if Config.DEBUG:
            string = "Integrated new BELIEF Task: " + j.get_formatted_string() + "from "
            for premise in j.stamp.parent_premises:
                string += str(premise) + ","
            Global.Global.debug_print(string)

            best_belief = task_statement_concept.belief_table.peek()
            if best_belief.is_event() and isinstance(best_belief.statement, NALGrammar.Terms.StatementTerm):
                print("Is " + str(j.statement) + " best belief positive? " + str(best_belief.is_positive()))

    def process_judgment_sentence(self, j1: NALGrammar.Sentences.Judgment, related_concept=None):
        """
            Continued processing for Judgment

            :param j1: Judgment
            :param related_concept: concept related to judgment with which to perform semantic inference
        """
        if Config.DEBUG:
            Global.Global.debug_print("Continued Processing JUDGMENT: " + str(j1))
            if j1.is_event() and isinstance(j1.statement, NALGrammar.Terms.StatementTerm):
                print("Is " + str(j1.statement) + " positive? " + str(j1.is_positive()))
        # get terms from sentence
        statement_term = j1.statement

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        # try a Revision on another belief in the table
        if not j1.is_event():
            j2 = statement_concept.belief_table.peek_highest_confidence_interactable(j1)
            if j2 is not None:
                if Config.DEBUG: Global.Global.debug_print(
                    "Revising belief: " + j1.get_formatted_string())
                derived_sentences = NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)
                for derived_sentence in derived_sentences:
                    self.global_buffer.put_new(NARSDataStructures.Other.Task(derived_sentence))

            # regular inference
            results = self.process_sentence_semantic_inference(j1, related_concept)
            for result in results:
                self.global_buffer.put_new(NARSDataStructures.Other.Task(result))



    def process_question_task(self, task, task_statement_concept):
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


    def process_goal_task(self, task: NARSDataStructures.Other.Task, task_statement_concept):
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
        current_desire = task_statement_concept.desire_table.take()

        if current_desire is None:
            best_desire = j
        elif NALGrammar.Sentences.may_interact(j,current_desire):
            # do a Revision
            best_desire =  NARSInferenceEngine.do_semantic_inference_two_premise(j, current_desire)[0]
        else:
            # choose the better desire
            best_desire = NALInferenceRules.Local.Choice(j, current_desire, only_confidence=True)

        # store the most confident desire
        task_statement_concept.desire_table.put(best_desire)

        if Config.DEBUG:
            string = "Integrated new GOAL Task: " + j.get_formatted_string() + "from "
            for premise in best_desire.stamp.parent_premises:
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
            if Config.DEBUG and statement.is_op():
                Global.Global.debug_print("Operation failed decision-making rule " + j.get_formatted_string())
            return  # Failed decision-making rule

        desire_event = statement_concept.belief_table.peek()
        if desire_event is not None:
            if desire_event.is_positive():
                if Config.DEBUG: Global.Global.debug_print(str(desire_event) + " is positive for goal: " + str(j))
                return  # Return if goal is already achieved


        if statement.is_op():
            self.queue_operation(j)
        else:
            if isinstance(statement, NALGrammar.Terms.CompoundTerm)\
                and NALSyntax.TermConnector.is_conjunction(statement.connector):
                # if it's a conjunction (A &/ B), simplify using true beliefs (e.g. A)
                subterm = statement.subterms[0]
                subterm_concept = Global.Global.NARS.memory.peek_concept(subterm)
                belief = subterm_concept.belief_table.peek()
                if belief is not None and belief.is_positive():
                    # the first component of the goal is positive, do inference and derive the remaining goal component
                    results = NARSInferenceEngine.do_semantic_inference_two_premise(j, belief)
                    for result in results:
                        # if result.statement.is_op():
                        #     self.process_goal_sentence(result)
                        self.global_buffer.put_new(NARSDataStructures.Other.Task(result))
                else:
                    pass
                    # # first component is not positive, but we want it to be
                    # new_goal = NALInferenceRules.HelperFunctions.create_resultant_sentence_one_premise(j=j,
                    #                                                                                   result_statement=subterm,
                    #                                                                                   truth_value_function=None)
                    # self.global_buffer.put_new(NARSDataStructures.Other.Task(new_goal))
            else:
                # process with random and context-relevant explanation A =/> B
                random_explanation_belief = self.memory.get_random_bag_explanation(j)
                contextual_explanation_belief = self.memory.get_explanation_preferred_with_true_precondition(j)

                if random_explanation_belief is not None:
                    if Config.DEBUG: Global.Global.debug_print(str(random_explanation_belief) + " is random explanation for " + str(j))
                    # process goal with explanation
                    results = NARSInferenceEngine.do_semantic_inference_two_premise(j, random_explanation_belief)
                    for result in results:
                        self.global_buffer.put_new(NARSDataStructures.Other.Task(result))

                if contextual_explanation_belief is not None:
                    if Config.DEBUG: Global.Global.debug_print(str(contextual_explanation_belief) + " is contextual explanation for " + str(j))
                    # process goal with explanation
                    results = NARSInferenceEngine.do_semantic_inference_two_premise(j, contextual_explanation_belief)
                    for result in results:
                        self.global_buffer.put_new(NARSDataStructures.Other.Task(result))

                if random_explanation_belief is None and contextual_explanation_belief is None:
                    if Config.DEBUG: Global.Global.debug_print("No explanations for " + str(j))



    def process_sentence_semantic_inference(self, j1, related_concept=None):
        """
            Processes a Sentence with a belief from a related concept.

            :param j1 - sentence to process
            :param related_concept - (Optional) concept from which to fetch a belief to process the sentence with

            #todo handle variables
        """
        if Config.DEBUG: Global.Global.debug_print("Processing: " + j1.get_formatted_string())
        statement_term = j1.statement
        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        j2s = []
        if related_concept is None:
            if Config.DEBUG: Global.Global.debug_print("Processing: Peeking randomly related concept")
            related_concepts = self.memory.get_semantically_related_concepts(statement_concept)
        else:
            if Config.DEBUG: Global.Global.debug_print("Processing: Using related concept " + str(related_concept))
            related_concepts = [related_concept]

        # check for a belief we can interact with
        for related_concept in related_concepts:
            j2 = related_concept.belief_table.peek()
            if NALGrammar.Sentences.may_interact(j1,j2):
                j2s.append(j2)
                break

        if len(j2s) == 0:
            if Config.DEBUG: Global.Global.debug_print('No related beliefs found for ' + j1.get_formatted_string())
            return []  # done if can't interact

        results = []
        for j2 in j2s:
            derived_sentences = NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)
            results += derived_sentences

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
        if self.current_operation_sequence is not None:
            # in the middle of a operation sequence already
            [_, current_sequence_desirability] = self.current_operation_sequence
            if desirability <= current_sequence_desirability: return # don't execute since the current sequence is more desirable
            # else, the given operation is more desirable
            self.operation_queue.clear()

        if Config.DEBUG:
            Global.Global.debug_print("Queueing operation: " + str(operation_goal))
        parent_strings = []
        # create an anticipation if this goal was based on a higher-order implication
        for parent in operation_goal.stamp.parent_premises:
            parent_strings.append(str(parent))

        # insert operation into queue to be execute after the interval
        # intervals of zero will result in immediate execution (assuming the queue is processed afterwards and in the same cycle as this function)
        if isinstance(operation_statement,NALGrammar.Terms.StatementTerm):
            # atomic op
            self.current_operation_sequence = [1, desirability] # 1 op to executre, desirability
            self.operation_queue.append([0, operation_statement, desirability, parent_strings])
        elif isinstance(operation_statement,NALGrammar.Terms.CompoundTerm):
            # higher-order operation like A &/ B or A &| B
            atomic_ops_left_to_execute = len(operation_statement.subterms)
            self.current_operation_sequence = [atomic_ops_left_to_execute, desirability]

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
        i = 0
        while i < len(self.operation_queue):
            remaining_working_cycles, operation_statement, desirability, parents = self.operation_queue[i]

            if remaining_working_cycles == 0:
                # operation is ready to execute
                self.execute_atomic_operation(operation_statement, desirability, parents)
                # now remove it from the queue
                self.operation_queue.pop(i)
                i -= 1
            else:
                # decrease remaining working cycles
                self.operation_queue[i][0] -= 1
            i += 1

        if len(self.operation_queue) == 0: self.current_operation_sequence = None


    def execute_atomic_operation(self, operation_statement_to_execute, desirability, parents):
        # execute an atomic operation immediately
        Global.Global.print_to_output("EXE: ^" + str(operation_statement_to_execute.get_predicate_term()) +
                                      " based on desirability: " + str(desirability) +
                                      " and parents: " + str(parents))

        if self.current_operation_sequence is not None: self.current_operation_sequence[0] -= 1

        # input the operation statement
        operation_event = NALGrammar.Sentences.Judgment(operation_statement_to_execute,
                                                        NALGrammar.Values.TruthValue(),
                                                        occurrence_time=Global.Global.get_current_cycle_number())
        InputChannel.process_sentence(operation_event)

