import math
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
        self.delay = 0  # delay between cycles
        self.atomic_operation_queue = [] # operations the system has queued to executed
        self.time = time.time()
        self.last_working_cycle = 0
        self.current_operation_sequence = None

    def run(self):
        """
            Infinite loop of working cycles
        """
        while True:
            if Config.gui_use_interface: self.handle_gui_pipes()
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
        if Config.gui_use_interface: Global.Global.NARS_string_pipe.send(("cycles", "Cycle #" + str(self.memory.current_cycle_number), None,0))

        InputChannel.process_pending_sentence()  # process strings coming from input buffer

        self.process_temporal_module()  # process events from the event buffer

        if time.time() - self.time > 1.0:
            self.time = time.time()
            print('Cycles per second: ' + str(Global.Global.get_current_cycle_number() - self.last_working_cycle))
            self.last_working_cycle = Global.Global.get_current_cycle_number()

        self.configure_busyness()

        # now do something with tasks from experience buffer and/or knowledge from memory
        for _ in range(Config.TASKS_PER_CYCLE):
            rand = random.random()
            if rand < Config.MINDFULNESS and len(self.global_buffer) > 0:
                # OBSERVE
                before = time.time()
                self.Observe()
                if Config.DEBUG: Global.Global.debug_print("Observe took " + str((time.time() - before)*1000) + "ms")
            else:
                # CONSIDER
                before = time.time()
                self.Consider()
                if Config.DEBUG: Global.Global.debug_print("Consider took " + str((time.time() - before) * 1000) + "ms")

        # if len(self.global_buffer) > 0:
        #     # process global buffer tasks
        #     for _ in range(Config.OBSERVES_PER_CYCLE):
        #         if len(self.global_buffer) > 0:
        #             # OBSERVE
        #             self.Observe()
        # else:
        #     for _ in range(Config.CONSIDERS_PER_CYCLE):
        #         self.Consider()

        # now execute operations
        self.execute_operation_queue()

        if Config.DEBUG:
            Global.Global.debug_print("global buffer: " + str(len(self.global_buffer)))

        # done
        self.memory.current_cycle_number += 1

    def configure_busyness(self):
        # X% full = X% focus
        Config.MINDFULNESS = max(0.75, len(self.global_buffer) / self.global_buffer.capacity)


    def do_working_cycles(self, cycles: int):
        """
            Performs the given number of working cycles.
        """
        for i in range(cycles):
            self.do_working_cycle()

    def process_temporal_module(self):
        """
            Process temporal chaining
        """
        if len(self.temporal_module) > 0:
            self.temporal_module.temporal_chaining_3()

        self.temporal_module.process_anticipations()


    def Observe(self):
        """
            Process a task from the global buffer
        """
        if len(self.global_buffer) > 0:
            task_item = self.global_buffer.take()

            # process task
            self.process_task(task_item.object)


    def Consider(self, concept=None):
        """
            Process a random concept in memory

            :param: concept: concept to consider. If None, picks a random concept
        """
        concept_item = None
        if concept is None:
            concept_item = self.memory.get_random_concept_item()
            if concept_item is None: return # nothing to ponder

            concept = concept_item.object

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
            if concept_item is not None: string += " $" + str(concept_item.budget.priority) + "$"
            if len(concept.belief_table) > 0: string += " expectation: " + str(concept.belief_table.peek().get_expectation())
            if len(concept.desire_table) > 0: string += " desirability: " + str(concept.desire_table.peek().get_desirability())
            Global.Global.debug_print(string)

        if concept is not None and attempts != max_attempts:
            #process a belief and desire
            #todo process both
            if len(concept.desire_table) > 0:
                sentence = concept.desire_table.peek()  # get most confident goal
                self.process_goal_sentence(sentence)
            elif len(concept.belief_table) > 0:
                sentence = concept.belief_table.peek()  # get most confident belief
                self.process_judgment_sentence(sentence)

            if len(concept.belief_table) > 0:
                s = concept.belief_table.peek()
                if Config.DEBUG and s.is_event() and isinstance(s.statement, NALGrammar.Terms.StatementTerm):
                    print("Is " + str(s.statement) + " positive? " + str(s.is_positive()))

        # decay priority; take concept out of bag and replace
        if concept_item is not None:
            concept_item = self.memory.concepts_bag.take_using_key(concept_item.key)
            concept_item.decay()
            self.memory.concepts_bag.put(concept_item)

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
                if Config.gui_use_interface:
                    Global.Global.clear_output_gui(data_structure=self.memory.concepts_bag)
                    for item in self.memory.concepts_bag:
                        if item not in self.memory.concepts_bag:
                            Global.Global.print_to_output(msg=str(item), data_structure=self.memory.concepts_bag)

                if Config.gui_use_interface:
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
            elif command == "delay":
                self.delay = key
            elif command == "paused":
                Global.Global.paused = key


    def process_task(self, task: NARSDataStructures.Other.Task):
        """
            Processes any Narsese task
        """
        Asserts.assert_task(task)

        sentence = task.sentence
        statement_term = sentence.statement
        if statement_term.contains_variable(): return  # todo handle variables

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept_item = self.memory.peek_concept_item(statement_term)
        statement_concept = statement_concept_item.object

        if isinstance(task.sentence, NALGrammar.Sentences.Judgment):
            self.process_judgment_task(task,statement_concept)
        elif isinstance(task.sentence, NALGrammar.Sentences.Question):
            self.process_question_task(task,statement_concept)
        elif isinstance(task.sentence, NALGrammar.Sentences.Goal):
            self.process_goal_task(task,statement_concept)

        if task.sentence.is_event():
            # increase priority; take concept out of bag and replace
            statement_concept_item = self.memory.concepts_bag.take_using_key(statement_concept_item.key)
            statement_concept_item.strengthen(Config.PRIORITY_STRENGTHEN_VALUE)
            self.memory.concepts_bag.put(statement_concept_item)

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

        # add the judgment itself into concept's belief table
        current_belief = task_statement_concept.belief_table.peek()

        best_belief = None
        if current_belief is None:
            best_belief = j
        elif NALGrammar.Sentences.may_interact(j,current_belief):
            # do a Revision
            revised_beliefs = NARSInferenceEngine.do_semantic_inference_two_premise(j, current_belief)
            if len(revised_beliefs) > 0:
                best_belief = revised_beliefs[0]
            else:
                best_belief = j

        else:
            if j.is_event():
                # choose the better desire
                best_belief = NALInferenceRules.Local.Choice(j,current_belief,only_confidence=True)
            else:
                # otherwise put it with the rest of the beliefs
                best_belief = j

        if j.is_event():
            # only keep one event
            current_belief = task_statement_concept.belief_table.take()

        task_statement_concept.belief_table.put(best_belief)

        if j.is_event():
            # anticipate event j
            self.temporal_module.anticipate_from_event(j)

        if Config.DEBUG:
            string = "Integrated BELIEF: " + best_belief.get_formatted_string() + "from "
            for premise in best_belief.stamp.parent_premises:
                string += str(premise) + ","
            Global.Global.debug_print(string)

            if best_belief.is_event() and isinstance(best_belief.statement, NALGrammar.Terms.StatementTerm):
                print("Is " + str(best_belief.statement) + " positive? " + str(best_belief.is_positive()))

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
            j2 = statement_concept.belief_table.peek_random()

            if NALGrammar.Sentences.may_interact(j1,j2):
                if Config.DEBUG: Global.Global.debug_print(
                    "Revising belief: " + j1.get_formatted_string())
                derived_sentences = NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)
                for derived_sentence in derived_sentences:
                    self.global_buffer.put_new(NARSDataStructures.Other.Task(derived_sentence))

        # results = self.process_sentence_semantic_inference(j1, related_concept)
        # for result in results:
        #     self.global_buffer.put_new(NARSDataStructures.Other.Task(result))
        #


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

        j1 = task.sentence

        """
            Initial Processing

            Insert it into the desire table or revise with the most confident desire
        """
        current_desire = task_statement_concept.desire_table.take()

        if current_desire is None:
            best_desire = j1
        elif NALGrammar.Sentences.may_interact(j1,current_desire):
            # do a Revision
            best_desire =  NARSInferenceEngine.do_semantic_inference_two_premise(j1, current_desire)[0]
        else:
            # choose the better desire
            best_desire = NALInferenceRules.Local.Choice(j1, current_desire, only_confidence=True)

        # store the most confident desire
        task_statement_concept.desire_table.put(best_desire)

        if Config.DEBUG:
            string = "Integrated GOAL: " + best_desire.get_formatted_string() + "from "
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
            if Config.DEBUG and statement.is_operation():
                Global.Global.debug_print("Operation failed decision-making rule " + j.get_formatted_string())
            return  # Failed decision-making rule

        desire_event = statement_concept.belief_table.peek()
        if desire_event is not None:
            if desire_event.is_positive():
                if Config.DEBUG: Global.Global.debug_print(str(desire_event) + " is positive for goal: " + str(j))
                return  # Return if goal is already achieved

        if statement.is_operation():
            self.queue_operation(j)
        else:
            if isinstance(statement, NALGrammar.Terms.CompoundTerm)\
                and NALSyntax.TermConnector.is_conjunction(statement.connector):
                # if it's a conjunction, simplify using true beliefs
                subterm = statement.subterms[0]
                subterm_concept = Global.Global.NARS.memory.peek_concept(subterm)
                belief = subterm_concept.belief_table.peek()
                if belief is not None and belief.is_positive():
                    # a component is positive, do inference and insert the remaining goal component
                    results = NARSInferenceEngine.do_semantic_inference_two_premise(j, belief)
                    for result in results:
                        self.global_buffer.put_new(NARSDataStructures.Other.Task(result))
                else:
                    # first component is not positive, but we want it to be
                    new_goal = NALInferenceRules.HelperFunctions.create_resultant_sentence_one_premise(j=j,
                                                                                                      result_statement=subterm,
                                                                                                      truth_value_function=None)
                    self.global_buffer.put_new(NARSDataStructures.Other.Task(new_goal))
            else:
                # process with highest-expectation explanation A =/> B
                best_explanation_belief = self.get_best_explanation_with_true_precondition(j)

                if best_explanation_belief is not None:
                    if Config.DEBUG: Global.Global.debug_print(str(best_explanation_belief) + " is best explanation for " + str(j))

                    # process goal with highest-expectation explanation
                    results = NARSInferenceEngine.do_semantic_inference_two_premise(j, best_explanation_belief)

                    for result in results:
                        self.global_buffer.put_new(NARSDataStructures.Other.Task(result))
                else:
                    if Config.DEBUG: Global.Global.debug_print("No best explanation for " + str(j))


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

    def get_best_explanation(self, j):
        """
            Gets the best explanation belief for the given sentence's statement
            that the sentence is able to interact with
        :param statement_concept:
        :return:
        """
        statement_concept: NARSMemory.Concept = self.memory.peek_concept(j.statement) # B
        best_explanation_belief = None
        for explanation_concept_item in statement_concept.explanation_links:
            explanation_concept: NARSMemory.Concept = explanation_concept_item.object  # A =/> B
            if len(explanation_concept.belief_table) == 0: continue

            belief = explanation_concept.belief_table.peek()

            if NALGrammar.Sentences.may_interact(j,belief):
                if best_explanation_belief is None:
                    best_explanation_belief = belief
                else:
                    best_explanation_belief = NALInferenceRules.Local.Choice(belief, best_explanation_belief)

        return best_explanation_belief

    def get_best_explanation_with_true_precondition(self, j):
        """
            Gets the best explanation belief for the given sentence's statement
            that the sentence is able to interact with
        :param statement_concept:
        :return:
        """
        statement_concept: NARSMemory.Concept = self.memory.peek_concept(j.statement) # B
        best_explanation_belief = None
        for explanation_concept_item in statement_concept.explanation_links:
            explanation_concept: NARSMemory.Concept = explanation_concept_item.object  # A =/> B

            belief = explanation_concept.belief_table.peek() # A =/> B

            if belief.statement.get_subject_term().contains_positive():
                if best_explanation_belief is None:
                    best_explanation_belief = belief
                else:
                    best_explanation_belief = NALInferenceRules.Local.Choice(belief, best_explanation_belief)

        return best_explanation_belief


    def get_random_positive_explanation(self, j):
        """
            Gets the best explanation belief for the given sentence's statement
            that the sentence is able to interact with
        :param statement_concept:
        :return:
        """
        concept: NARSMemory.Concept = self.memory.peek_concept(j.statement) # B
        positive_beliefs = []
        for explanation_concept_item in concept.explanation_links:
            explanation_concept = explanation_concept_item.object
            if len(explanation_concept.belief_table ) == 0: continue
            explanation_belief = explanation_concept.belief_table.peek()

            if explanation_belief is not None:
                if explanation_belief.is_positive():
                    positive_beliefs.append(explanation_belief)

        if len(positive_beliefs) == 0:
            return None
        return positive_beliefs[round(random.random() * (len(positive_beliefs)-1))]

    def get_best_prediction(self, j):
        """
            Returns the best prediction belief for a given belief
        :param j:
        :return:
        """
        concept = self.memory.peek_concept(j.statement)
        best_belief = None
        for prediction_concept_item in concept.prediction_links:
            prediction_concept = prediction_concept_item.object
            if len(prediction_concept.belief_table ) == 0: continue
            prediction_belief = prediction_concept.belief_table.peek()

            if prediction_belief is not None:
                if best_belief is None:
                    best_belief = prediction_belief
                else:
                    best_belief = NALInferenceRules.Local.Choice(best_belief, prediction_belief) # new best belief?

        return best_belief

    def get_random_positive_prediction(self, j):
        """
            Returns a random positive prediction belief for a given belief
        :param j:
        :return:
        """
        concept = self.memory.peek_concept(j.statement)
        positive_beliefs = []
        for prediction_concept_item in concept.prediction_links:
            prediction_concept = prediction_concept_item.object
            if len(prediction_concept.belief_table) == 0: continue
            prediction_belief = prediction_concept.belief_table.peek()

            if prediction_belief is not None:
                if prediction_belief.is_positive():
                    positive_beliefs.append(prediction_belief)

        if len(positive_beliefs) == 0:
            return None
        return positive_beliefs[round(random.random() * (len(positive_beliefs)-1))]

    def get_all_positive_predictions(self, j):
        predictions = []
        concept = self.memory.peek_concept(j.statement)
        for prediction_concept_item in concept.prediction_links:
            prediction_concept = prediction_concept_item.object
            if len(prediction_concept.belief_table ) == 0: continue
            prediction_belief = prediction_concept.belief_table.peek()

            if prediction_belief is not None:
                if isinstance(prediction_belief.statement.get_predicate_term(),NALGrammar.Terms.StatementTerm) and prediction_belief.is_positive():
                    predictions.append(prediction_belief)

        return predictions

    def get_best_desired_prediction(self, concept):
        """
            Returns the best predictive implication from a given concept's prediction links,
            but only accounts those predictions whose postconditions are desired
        :param j:
        :return:
        """
        best_belief = None
        for prediction_concept_item in concept.prediction_links:
            prediction_concept = prediction_concept_item.object
            if len(prediction_concept.belief_table ) == 0: continue
            prediction_belief = prediction_concept.belief_table.peek()

            if prediction_belief is not None:
                postcondition_term = prediction_concept.term.get_predicate_term()
                if isinstance(postcondition_term,NALGrammar.Terms.StatementTerm) and prediction_concept.is_positive():
                    if self.memory.peek_concept(postcondition_term).is_desired():
                        if best_belief is None:
                            best_belief = prediction_belief
                        else:
                            best_belief = NALInferenceRules.Local.Choice(best_belief, prediction_belief) # new best belief?

        return best_belief

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
        # full_operation_term.get_subject_term()
        operation_statement = operation_goal.statement
        desirability = operation_goal.get_desirability()
        if self.current_operation_sequence is not None:
            # in the middle of a operation sequence already
            [_, current_sequence_desirability] = self.current_operation_sequence
            if desirability <= current_sequence_desirability: return # don't execute since the current sequence is more desirable
            # else, the given operation is more dresirable
            self.atomic_operation_queue.clear()

        parent_strings = []
        # create an anticipation if this goal was based on a higher-order implication
        for parent in operation_goal.stamp.parent_premises:
            parent_strings.append(str(parent))

        # insert operation into queue to be execute after the interval
        # intervals of zero will result in immediate execution (assuming the queue is processed afterwards and in the same cycle as this function)
        if isinstance(operation_statement,NALGrammar.Terms.StatementTerm):
            self.current_operation_sequence = None
            self.atomic_operation_queue.append([0, operation_statement, desirability, parent_strings])
        elif isinstance(operation_statement,NALGrammar.Terms.CompoundTerm):
            # higher-order operation like A &/ B or A &| B
            atomic_ops_left_to_execute = len(operation_statement.subterms)
            self.current_operation_sequence = [atomic_ops_left_to_execute, desirability]

            working_cycles = 0
            for i in range(len(operation_statement.subterms)):
                # insert the atomic subterm operations and their working cycle delays
                subterm = operation_statement.subterms[i]
                self.atomic_operation_queue.append([working_cycles, subterm, desirability, parent_strings])
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
        while i < len(self.atomic_operation_queue):
            remaining_working_cycles, operation_statement, desirability, parents = self.atomic_operation_queue[i]

            if remaining_working_cycles == 0:
                # operation is ready to execute
                self.execute_atomic_operation(operation_statement, desirability, parents)
                # now remove it from the queue
                self.atomic_operation_queue.pop(i)
                i -= 1
            else:
                # decrease remaining working cycles
                self.atomic_operation_queue[i][0] -= 1
            i += 1


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

