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
from NALInferenceRules import TruthValueFunctions
from NALInferenceRules.HelperFunctions import create_resultant_sentence_one_premise

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
        self.event_buffer = NARSDataStructures.Buffers.EventBuffer(item_type=NARSDataStructures.Other.Task, capacity=Config.EVENT_BUFFER_CAPACITY)
        self.memory = NARSMemory.Memory()
        self.delay = 0  # delay between cycles

    def run(self):
        """
            Infinite loop of working cycles
        """
        while True:
            self.handle_gui_pipes()
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
        if Global.Global.gui_use_interface: Global.Global.NARS_string_pipe.send(("cycles", "Cycle #" + str(self.memory.current_cycle_number), None,0))

        InputChannel.process_pending_sentence()  # process strings coming from input buffer

        self.process_event_buffer()  # process events from the event buffer

        # now do something with tasks from experience buffer and/or knowledge from memory
        for _ in range(Config.ACTIONS_PER_CYCLE):
            self.Consider()

        self.memory.current_cycle_number += 1


    def do_working_cycles(self, cycles: int):
        """
            Performs the given number of working cycles.
        """
        for i in range(cycles):
            self.do_working_cycle()

    def process_event_buffer(self):
        """
            Process events into the global buffer
        """
        # temporal chaining
        self.event_buffer.process_temporal_chaining(NARS=self)


    def Consider(self):
        """
            Process a random concept in memory
        """
        concept_item = self.memory.get_random_concept()

        if concept_item is None: return  # nothing to ponder

        concept_to_consider: NARSMemory.Concept  = concept_item.object

        if not isinstance(concept_item.object.term, NALGrammar.Terms.StatementTerm):
            # Concept is not named by a statement, get a related statement concept
            if len(concept_to_consider.term_links) > 0:
                concept_to_consider = concept_to_consider.term_links.peek().object
            else:
                concept_to_consider = None

        if concept_to_consider is not None:
            #process a belief and desire
            if len(concept_to_consider.belief_table) > 0:
                sentence = concept_to_consider.belief_table.take()  # get most confident belief
                self.process_judgment_sentence(sentence)
                concept_to_consider.belief_table.put(sentence)

            if len(concept_to_consider.desire_table) > 0:
                sentence = concept_to_consider.desire_table.peek()  # get most confident goal
                self.process_goal_sentence(sentence)

                # decay priority; take concept out of bag and replace
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
                if Global.Global.gui_use_internal_data:
                    Global.Global.clear_output_gui(data_structure=self.memory.concepts_bag)
                    for item in self.memory.concepts_bag:
                        if item not in self.memory.concepts_bag:
                            Global.Global.print_to_output(msg=str(item), data_structure=self.memory.concepts_bag)

                if Global.Global.gui_use_interface:
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
                if data_structure_id == str(self.event_buffer):
                    data_structure = self.event_buffer
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
                item = self.memory.concepts_bag.peek(key)
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

        # increase priority; take concept out of bag and replace
        statement_concept_item = self.memory.concepts_bag.take_using_key(statement_concept_item.key)
        statement_concept_item.strengthen()
        self.memory.concepts_bag.put(statement_concept_item)

    def process_judgment_task(self, task: NARSDataStructures.Other.Task, task_statement_concept):
        """
            Processes a Narsese Judgment Task
            Insert it into the belief table and revise it with another belief

            :param Judgment Task to process
        """
        Asserts.assert_task(task)

        j1 = task.sentence

        # commented out because it floods the system
        #derived_sentences = NARSInferenceEngine.do_inference_one_premise(j1)
        #for derived_sentence in derived_sentences:
        #   self.global_task_buffer.put_new(NARSDataStructures.Other.Task(derived_sentence))

        # add the judgment itself into concept's belief table
        current_belief = task_statement_concept.belief_table.take()

        if current_belief is None:
            revised_belief = j1
        elif NALGrammar.Sentences.may_interact(j1,current_belief):
            # do a Revision
            revised_beliefs = NARSInferenceEngine.do_semantic_inference_two_premise(j1, current_belief)
            if len(revised_beliefs) > 0:
                revised_belief = revised_beliefs[0]
            else:
                revised_belief = j1
        else:
            # choose the better desire
            revised_belief = NALInferenceRules.Local.Choice(j1,current_belief)

        # store the most confident desire
        task_statement_concept.belief_table.put(revised_belief)

        #task_statement_concept.belief_table.put(j1)


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

        statement_term = task.sentence.statement
        if statement_term.connector == NALSyntax.TermConnector.SequentialConjunction:
            # derive individual components from conjunction &/
            for subterm in statement_term.subterms:
                self.process_task(NARSDataStructures.Other.Task(create_resultant_sentence_one_premise(j1,
                                                                                    subterm,
                                                                                    truth_value_function=None)))

        """
            Initial Processing

            Insert it into the desire table or revise with the most confident desire
        """
        current_desire = task_statement_concept.desire_table.take()

        if current_desire is None:
            revised_desire = j1
        elif NALGrammar.Sentences.may_interact(j1,current_desire):
            # do a Revision
            revised_desire = NARSInferenceEngine.do_semantic_inference_two_premise(j1, current_desire)[0]
        else:
            # choose the better desire
            revised_desire = NALInferenceRules.Local.Choice(j1,current_desire)

        # store the most confident desire
        task_statement_concept.desire_table.put(revised_desire)

        if isinstance(revised_desire, NALGrammar.Sentences.Goal):
            string = "PROCESSED GOAL: " + revised_desire.get_formatted_string() + "from "
            for premise in revised_desire.stamp.parent_premise_strings:
                string += premise + ","
            print(string)

    def process_judgment_sentence(self, j1: NALGrammar.Sentences.Judgment, related_concept=None):
        """
            Continued processing for Judgment

            :param j1: Judgment
            :param related_concept: concept related to judgment with which to perform semantic inference
        """

        # get terms from sentence
        statement_term = j1.statement

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept_item(statement_term).object

        # do a Revision
        if not j1.is_event():
            j2 = None
            for (belief, confidence) in statement_concept.belief_table:
                if NALGrammar.Sentences.may_interact(j1, belief):
                    j2 = belief  # belief can interact with j1
                    break

            if j2 is not None:
                if Config.DEBUG: print(
                    "Revising belief: " + j1.get_formatted_string())
                derived_sentences = NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)
                for derived_sentence in derived_sentences:
                    self.process_task(NARSDataStructures.Other.Task(derived_sentence))

        results = self.process_sentence_semantic_inference(j1, related_concept)
        for result in results:
            self.process_task(NARSDataStructures.Other.Task(result))

    def process_goal_sentence(self, j1: NALGrammar.Sentences.Goal):
        """
            Continued processing for Goal

            :param j1: Goal
            :param related_concept: concept related to goal with which to perform semantic inference
        """
        statement_term = j1.statement
        statement_concept: NARSMemory.Concept = self.memory.peek_concept_item(statement_term).object

        # see if it should be pursued
        should_pursue = NALInferenceRules.Local.Decision(j1)
        if not should_pursue: return  # Failed decision-making rule

        desire_event = statement_concept.belief_table.take()
        if desire_event is not None:
            statement_concept.belief_table.put(desire_event) #re-insert into table
            if desire_event.is_positive(): return  # Return if goal is already achieved

        if statement_term.is_operation():
            self.execute_operation(j1)
        else:
            best_explanation = None
            for explanation_concept_item in statement_concept.explanation_links:
                explanation_concept: NARSMemory.Concept = explanation_concept_item.object
                explanation_confidence = explanation_concept.belief_table.peek().value.confidence
                precondition_statement = explanation_concept.belief_table.peek().statement.get_subject_term()

                if precondition_statement.connector == NALSyntax.TermConnector.SequentialConjunction:
                    # conjunction &/
                    for subterm in precondition_statement.subterms:
                        subterm_concept = self.memory.peek_concept_item(subterm).object
                        if subterm_concept.is_positive():
                            # strengthen for every positive precondition element
                            explanation_confidence = NALInferenceRules.ExtendedBooleanOperators.bor(explanation_confidence, Config.CONFIDENCE_STRENGTHEN_VALUE)
                            print('PREMISE IS TRUE: ' + str(subterm))

                if best_explanation is None \
                    or (explanation_confidence > best_explanation.belief_table.peek().value.confidence):
                    # this is better than the best explanation found so far
                    best_explanation = explanation_concept


            # process with highest-confidence explanation
            results = self.process_sentence_semantic_inference(j1, best_explanation)

            for result in results:
                self.process_task(NARSDataStructures.Other.Task(result))


    def process_sentence_semantic_inference(self, j1, related_concept=None):
        """
            Processes a Sentence with a belief from a related concept.

            :param j1 - sentence to process
            :param related_concept - (Optional) concept from which to fetch a belief to process the sentence with

            #todo handle variables
        """
        if Config.DEBUG: print("Processing: " + j1.get_formatted_string())
        statement_term = j1.statement
        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept_item(statement_term).object

        j2s = []
        if related_concept is None:
            related_concepts = self.memory.get_semantically_related_concepts(statement_concept)
        else:
            related_concepts = [related_concept]

        # check for a belief we can interact with
        for related_concept in related_concepts:
            for (belief, confidence) in related_concept.belief_table:
                if NALGrammar.Sentences.may_interact(j1, belief):
                    j2s.append(belief)  # belief can interact with j1, store it and move onto next related concept
                    break

        if len(j2s) == 0:
            if Config.DEBUG: print('No related beliefs found for ' + j1.get_formatted_string())
            return []  # done if can't interact

        results = []
        for j2 in j2s:
            if Config.DEBUG: print(
                "Trying inference between: " + j1.get_formatted_string() + " and " + j2.get_formatted_string())
            derived_sentences = NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)
            results += derived_sentences

        return results

    def execute_operation(self, operation_goal):
        """

        :param operation_goal: Including SELF, arguments, and Operation itself
        :return:
        """
        # todo extract and use args
        # full_operation_term.get_subject_term()
        operation = operation_goal.statement.get_predicate_term()
        value = operation_goal.get_value_projected_to_current_time()
        desirability = TruthValueFunctions.Expectation(value.frequency, value.confidence)
        Global.Global.print_to_output("EXE: ^" + str(operation) + " based on desirability: " + str(desirability))
        operation_event = NALGrammar.Sentences.Judgment(operation_goal.statement, NALGrammar.Values.TruthValue(),
                                                        occurrence_time=Global.Global.get_current_cycle_number())
        operation_task = NARSDataStructures.Other.Task(operation_event)
        self.event_buffer.put_new(operation_task)
        self.process_task(operation_task)
