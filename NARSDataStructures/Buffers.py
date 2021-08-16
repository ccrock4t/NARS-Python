"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import NALSyntax
import NARSInferenceEngine
from NARSDataStructures.ItemContainers import ItemContainer, Item
from NARSDataStructures.Other import Depq, Task
import NALInferenceRules

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

class EventBuffer(ItemContainer):
    """
        FIFO that performs temporal composition
    """
    def __init__(self, item_type, capacity):
        ItemContainer.__init__(self,item_type=item_type,capacity=capacity)
        self.fifo = [] # stores events
        # temporal chaining
        self.temporal_chain = []
        self.temporal_chain_max_results_length = capacity * (capacity + 1) / 2 - 1 # maximum number of results created by temporal chaining
        self.temporal_chain_has_changes = False # have any changes to the temporal chain since last time it was processed?

    def __len__(self):
        return len(self.fifo)

    def __iter__(self):
        return iter(self.fifo)

    def __getitem__(self, index):
        return self.fifo[index]

    def put(self, item):
        """
            Put the newest item onto the end of the buffer.

            :returns Item that was purged if the inserted item caused an overflow
        """
        if not isinstance(item, Item):
            item = Item(item, self.get_next_item_id())

        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)

        # add to buffer
        self.fifo.append(item)
        ItemContainer._put_into_lookup_dict(self, item)  # Item Container

        purged_item = None
        if len(self) > self.capacity:
            purged_item = self.take()

        # update temporal chain
        self.temporal_chain.append(item)
        self.temporal_chain_has_changes = True
        if len(self.temporal_chain) > self.capacity:
            self.temporal_chain.pop(0)

        return purged_item

    def take(self):
        """
            Take the oldest item from the Buffer
            :return:
        """
        if len(self) == 0: return None
        item = self.fifo.pop(0)
        self._take_from_lookup_dict(item.key)
        return item

    def process_temporal_chaining(self, NARS=None):
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
        results = []
        temporal_chain = self.temporal_chain
        num_of_events = len(temporal_chain)

        event_task_C = temporal_chain[-1].object
        event_C = event_task_C.sentence

        def process_sentence(derived_sentence):
            if derived_sentence is not None:
                results.append(derived_sentence)
                if NARS is not None: NARS.process_task(Task(derived_sentence))

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