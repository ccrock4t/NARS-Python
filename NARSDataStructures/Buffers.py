"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import Config
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

        Depq._insert_object(self, item, item.budget.priority) # Depq
        ItemContainer._put_into_lookup_dict(self, item)  # Item Container

        purged_item = None
        if len(self) > self.capacity:
            purged_item = self._extract_min()
            self._take_from_lookup_dict(purged_item.key)

        return purged_item

    def take(self):
        """
            Take the max priority item
            :return:
        """
        if len(self) == 0: return None
        item = Depq._extract_max(self)
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
        self.anticipations_list = []

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


    def temporal_chaining(self):
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
                if NARS is not None: NARS.global_buffer.put_new(Task(derived_sentence))

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
                process_sentence(derived_sentence)

            for j in range(i + 1, num_of_events-1):
                event_task_B = temporal_chain[j].object
                event_B = event_task_B.sentence

                conjunction = NALInferenceRules.Temporal.TemporalIntersection(event_A,
                                                                                event_B)  # (A &/ B)

                if conjunction is not None:
                    derived_sentence = NALInferenceRules.Temporal.TemporalInduction(conjunction,
                                                                                    event_C)  # (A &/ B) =/> C
                    process_sentence(derived_sentence)

        self.temporal_chain_has_changes = False

        return results

    def anticipate(self):
        """
            anticipation (negative evidence for predictive implications)
        """
        # process pending anticipations
        i = 0
        while i < len(self.anticipations_list):
            remaining_cycles, best_prediction_concept, anticipated_event_term = self.anticipations_list[i] # event we expect to occur
            anticipation_concept = self.NARS.memory.peek_concept(anticipated_event_term)
            if remaining_cycles == 0:
                if anticipation_concept.is_positive():
                    # confirmed
                    pass
                else:
                    if Config.DEBUG: print(str(anticipation_concept) + " DISAPPOINT - FAILED ANTICIPATION, NEGATIVE EVIDENCE FOR " + str(best_prediction_concept.term))
                    self.NARS.global_buffer.put_new(Task(NALGrammar.Sentences.Judgment(statement=best_prediction_concept.term,
                                                  value=NALGrammar.Values.TruthValue(frequency=0.0, confidence=0.5))))
                self.anticipations_list.pop(i)
                i -= 1
            else:
                self.anticipations_list[i][0] -= 1

            i += 1

        # and form new anticipations
        # todo compound events, this only happens with atomic events
        observed_event = self.get_most_recent_event_task()
        observed_event = observed_event.sentence

        best_prediction_concept = None
        for prediction_concept_item in self.NARS.memory.peek_concept(observed_event.statement).prediction_links:
            prediction_concept = prediction_concept_item.object
            if isinstance(prediction_concept.term.get_predicate_term(),NALGrammar.Terms.StatementTerm) and prediction_concept.is_positive():
                if best_prediction_concept is None:
                    best_prediction_concept= prediction_concept
                else:
                    if prediction_concept.belief_table.peek().value.confidence > best_prediction_concept.belief_table.peek().value.confidence:
                        best_prediction_concept = prediction_concept

        if best_prediction_concept is None: return # nothing is anticipated

        # something is anticipated
        postcondition = best_prediction_concept.term.get_predicate_term()
        print(str(postcondition) +  " IS ANTICIPATED FROM " + str(best_prediction_concept.belief_table.peek()))
        self.anticipations_list.append([NALInferenceRules.HelperFunctions.convert_from_interval(postcondition.interval+1),best_prediction_concept, postcondition])


