"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import time

import Config
import Global
import NALSyntax
import NARSInferenceEngine
from NARSDataStructures.ItemContainers import ItemContainer, Item
from NARSDataStructures.Other import Depq, Task
import NALInferenceRules
import NALGrammar

class Buffer(ItemContainer, Depq):
    """
        Priority-Queue
    """
    def __init__(self, item_type, capacity):
        self.capacity=capacity
        ItemContainer.__init__(self, item_type=item_type,capacity=capacity) # Item Container
        Depq.__init__(self) #Depq


    def put(self, item):
        """
            Insert an Item into the Buffer, sorted by priority.

            :returns Item that was purged if the inserted item caused an overflow
        """
        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)

        Depq.insert_object(self, item, item.budget.get_priority()) # Depq
        ItemContainer._put_into_lookup_dict(self, item)  # Item Container

        purged_item = None
        if len(self) > self.capacity:
            purged_item = self.extract_min()
            self._take_from_lookup_dict(purged_item.key)

        return purged_item

    def take(self):
        """
            Take the max priority item
            :return:
        """
        if len(self) == 0: return None
        item = Depq.extract_max(self)
        self._take_from_lookup_dict(item.key)
        return item

    def peek(self, key):
        """
            Peek item with highest priority
            O(1)

            Returns None if depq is empty
        """
        if len(self) == 0: return None
        if key is None:
            return Depq.peek_max(self)
        else:
            return ItemContainer.peek_using_key(self, key=key)

class TemporalModule(ItemContainer):
    """
        Performs
            temporal composition
                and
            anticipation (negative evidence for predictive implications)
    """
    def __init__(self, NARS, item_type, capacity):
        ItemContainer.__init__(self,item_type=item_type,capacity=capacity)

        self.NARS = NARS
        # temporal chaining
        self.temporal_chain = []
        self.temporal_chain_max_results_length = capacity * (capacity + 1) / 2 - 1 # maximum number of results created by temporal chaining
        self.temporal_chain_has_changes = False # have any changes to the temporal chain since last time it was processed?

        # anticipation
        self.anticipations_queue = []
        self.current_anticipation = None

    def __len__(self):
        return len(self.temporal_chain)

    def __iter__(self):
        return iter(self.temporal_chain)

    def __getitem__(self, index):
        return self.temporal_chain[index]

    def put(self, item):
        """
            Put the newest item onto the end of the buffer.

            :returns Item that was purged if the inserted item caused an overflow
        """
        if not isinstance(item, Item):
            item = Item(item, self.get_next_item_id())

        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)

        # add to buffer
        self.temporal_chain.append(item)
        self.temporal_chain_has_changes = True
        ItemContainer._put_into_lookup_dict(self, item)  # Item Container

        # update temporal chain
        if len(self.temporal_chain) > self.capacity:
            self.temporal_chain.pop(0)

        return

    def get_most_recent_event_task(self):
        return self.temporal_chain[-1].object



    def temporal_chaining_3(self):
        """
            Perform temporal chaining

            produce all possible forward implication statements using temporal induction and intersection
                A &/ B,
                A =/> B
                and
                (A &/ B) =/> C

            for the latest statement in the chain
        """
        if not self.temporal_chain_has_changes: return []
        NARS = self.NARS
        results = []
        temporal_chain = self.temporal_chain
        num_of_events = len(temporal_chain)

        event_task_C = self.get_most_recent_event_task()
        event_C = event_task_C.sentence

        def process_sentence(derived_sentence):
            if derived_sentence is not None:
                results.append(derived_sentence)
                if NARS is not None:
                    task = Task(derived_sentence)
                    NARS.global_buffer.put_new(task)

        # produce all possible forward implication statements using temporal induction and intersection
        # A &/ C,
        # A =/> C
        # and
        # (A &/ B) =/> C
        for i in range(0, num_of_events-1):  # and do induction with events occurring afterward
            event_task_A = temporal_chain[i].object
            event_A = event_task_A.sentence

            # produce statements (A =/> C) and (A &/ C)
            derived_sentences = NARSInferenceEngine.do_temporal_inference_two_premise(event_A, event_C)


            for derived_sentence in derived_sentences:
                #if isinstance(derived_sentence.statement, NALGrammar.Terms.StatementTerm): continue  # ignore simple implications
                process_sentence(derived_sentence)

            for j in range(i + 1, num_of_events-1):
                event_task_B = temporal_chain[j].object
                event_B = event_task_B.sentence

                conjunction_A_B = NALInferenceRules.Temporal.TemporalIntersection(event_A,
                                                                                  event_B)  # (A &/ B)

                if conjunction_A_B is not None and NALSyntax.TermConnector.is_conjunction(conjunction_A_B.statement.connector):
                    derived_sentence = NALInferenceRules.Temporal.TemporalInduction(conjunction_A_B,
                                                                                    event_C)  # (A &/ B) =/> C
                    process_sentence(derived_sentence)

        self.temporal_chain_has_changes = False

        return results


    def temporal_chaining_4(self):
        """
            Perform temporal chaining

            produce all possible forward implication statements using temporal induction and intersection
                A &/ D,
                A =/> D
                and
                (A &/ B) =/> D
                (A &/ C) =/> D
                and
                (A &/ B &/ C) =/> D

            for the latest event D in the chain
        """
        if not self.temporal_chain_has_changes: return []
        NARS = self.NARS
        results = []
        temporal_chain = self.temporal_chain
        num_of_events = len(temporal_chain)

        event_task_D = self.get_most_recent_event_task()
        event_D = event_task_D.sentence

        def process_sentence(derived_sentence):
            if derived_sentence is not None:
                results.append(derived_sentence)
                if NARS is not None:
                    task = Task(derived_sentence)
                    NARS.global_buffer.put_new(task)

        # produce all possible forward implication statements using temporal induction and intersection
        # A &/ C,
        # A =/> C
        # and
        # (A &/ B) =/> C
        for i in range(0, num_of_events-1):  # and do induction with events occurring afterward
            event_task_A = temporal_chain[i].object
            event_A = event_task_A.sentence

            # produce statements (A =/> D) and (A &/ D)
            derived_sentences = NARSInferenceEngine.do_temporal_inference_two_premise(event_A, event_D)

            for derived_sentence in derived_sentences:
                process_sentence(derived_sentence)

            for j in range(i + 1, num_of_events-1):
                event_task_B = temporal_chain[j].object
                event_B = event_task_B.sentence

                conjunction_A_B = NALInferenceRules.Temporal.TemporalIntersection(event_A,
                                                                                event_B)  # (A &/ B)
                if conjunction_A_B is not None:
                    derived_sentence = NALInferenceRules.Temporal.TemporalInduction(conjunction_A_B,
                                                                                    event_D)  # (A &/ B) =/> D
                    process_sentence(derived_sentence)


                for k in range(j + 1, num_of_events - 1):
                    if conjunction_A_B is None: break
                    event_task_C = temporal_chain[k].object
                    event_C = event_task_C.sentence
                    conjunction_A_B_C = NALInferenceRules.Temporal.TemporalIntersection(conjunction_A_B,
                                                                                        event_C)  # (A &/ B &/ C)
                    derived_sentence = NALInferenceRules.Temporal.TemporalInduction(conjunction_A_B_C,
                                                                                    event_D)  # (A &/ B &/ C) =/> D
                    process_sentence(derived_sentence)

        self.temporal_chain_has_changes = False

        return results

    def anticipate_from_event(self, observed_event):
        """
            # form new anticipation from observed event
        """
        if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()

        random_prediction = self.NARS.memory.get_random_bag_prediction(observed_event)

        if random_prediction is not None:
            # something is anticipated
            self.anticipate_from_concept(self.NARS.memory.peek_concept(random_prediction.statement),
                                         random_prediction)


        if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
            "Forming anticipation from event took " + str((time.time() - before) * 1000) + "ms")




    def anticipate_from_concept(self, higher_order_anticipation_concept, best_belief=None):
        """
            Form an anticipation based on a higher-order concept.
            Uses the best belief from the belief table, unless one is provided.

        :param higher_order_anticipation_concept:
        :param best_belief:
        :return:
        """

        if best_belief is None:
            best_belief = higher_order_anticipation_concept.belief_table.peek()

        expectation = best_belief.get_expectation()

        # use this for 1 anticipation only
        # if self.current_anticipation is not None:
        #     # in the middle of a operation sequence already
        #     current_anticipation_expectation = self.current_anticipation
        #     if expectation <= current_anticipation_expectation: return # don't execute since the current anticipation is more expected
        #     # else, the given operation is more expected
        #     self.anticipations_queue.clear()

        self.current_anticipation = expectation

        working_cycles = NALInferenceRules.HelperFunctions.convert_from_interval(higher_order_anticipation_concept.term.interval)

        postcondition = higher_order_anticipation_concept.term.get_predicate_term()
        self.anticipations_queue.append([working_cycles, higher_order_anticipation_concept, postcondition])
        if Config.DEBUG: Global.Global.debug_print(str(postcondition) + " IS ANTICIPATED FROM " + str(best_belief) + " Total Anticipations:" + str(len(self.anticipations_queue)))

    def process_anticipations(self):
        """

            anticipation (negative evidence for predictive implications)
        """
        # process pending anticipations
        i = 0

        while i < len(self.anticipations_queue):
            remaining_cycles, best_prediction_concept, anticipated_postcondition = self.anticipations_queue[i] # event we expect to occur
            anticipated_postcondition_concept = self.NARS.memory.peek_concept(anticipated_postcondition)
            if remaining_cycles == 0:
                if anticipated_postcondition_concept.is_positive():
                    # confirmed
                    if Config.DEBUG: Global.Global.debug_print(
                        str(anticipated_postcondition_concept) + " SATISFIED - CONFIRMED ANTICIPATION" + str(
                            best_prediction_concept.term))
                else:
                    sentence = NALGrammar.Sentences.Judgment(statement=best_prediction_concept.term,
                                                  value=NALGrammar.Values.TruthValue(frequency=0.0,
                                                                                     confidence=Config.DEFAULT_DISAPPOINT_CONFIDENCE))
                    if Config.DEBUG:
                        Global.Global.debug_print(str(anticipated_postcondition_concept) + " DISAPPOINT - FAILED ANTICIPATION, NEGATIVE EVIDENCE FOR " + str(sentence))
                    self.NARS.global_buffer.put_new(Task(sentence))
                self.anticipations_queue.pop(i)
                self.current_anticipation = None
                i -= 1
            else:
                self.anticipations_queue[i][0] -= 1

            i += 1




