"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
from NARSDataStructures.ItemContainers import ItemContainer, Item
from NARSDataStructures.Other import Depq
import Config
import queue

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
        self.fifo = []

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

        self.fifo.append(item)
        ItemContainer._put_into_lookup_dict(self, item)  # Item Container

        purged_item = None
        if len(self) > self.capacity:
            purged_item = self.take()

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

    def clear(self):
        """
            Empty the buffer.
        """
        while len(self) > 0:
            self.take()