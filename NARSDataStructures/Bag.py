"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import heapq
import random
from bisect import bisect

import NARSDataStructures.ItemContainers

class Bag(NARSDataStructures.ItemContainers.ItemContainer):
    """
        Probabilistic priority-queue

        --------------------------------------------

        An array of buckets, where each bucket holds items of a certain priority
        (e.g. 100 buckets, bucket 1 - hold items with 0.01 priority,  bucket 50 - hold items with 0.50 priority)
    """

    def __init__(self, item_type, capacity):
        self.items = [] # cumulative weights of non-empty buckets
        self.count = 0
        self.ordered_items = NARSDataStructures.Other.Depq()
        NARSDataStructures.ItemContainers.ItemContainer.__init__(self, item_type=item_type,capacity=capacity)

    def __len__(self):
        return self.count

    def __iter__(self):
        return iter(list(self.item_lookup_dict.values()).__reversed__())

    def put(self, item):
        """
            Place a NEW Item into the bag.

            :param Bag Item to place into the Bag
            :returns Item purged from the Bag if the inserted item causes an overflow
        """
        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)

        # increase Bag count
        self.count += 1

        NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self, item)  # Item Container
        # put item into bag (priority times)
        idx_to_add = bisect(self.items, item.key)
        for i in range(int(100*item.budget.priority)):
            self.items.insert(idx_to_add,item.key)

        self.ordered_items.insert_object(item, item.budget.priority)

        # remove lowest priority item if over capacity
        purged_item = None
        if len(self) > self.capacity:
            purged_item = self._take_min()

        return purged_item

    def peek(self, key=None):
        """
            Peek an object from the bag using its key.
            If key is None, peeks probabilistically

            :returns An item peeked from the Bag; None if item could not be peeked from the Bag
        """
        if self.count == 0: return None  # no items

        if key is None:
            item = self._peek_probabilistically()
        else:
            item = NARSDataStructures.ItemContainers.ItemContainer.peek_using_key(self,key=key)

        return item

    def strengthen_item(self, key):
        """
            Decays an item in the bag
        :param key:
        :return:
        """
        concept_item = self.peek_using_key(key)
        before = concept_item.get_bag_number()
        NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        concept_item.strengthen()
        NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self, concept_item)
        after = concept_item.get_bag_number()
        diff = abs(after - before)
        # remove the difference in priority so its less likely to be randomly selected
        idx_to_add = bisect(self.items, key)
        for i in range(diff):
            self.items.insert(idx_to_add,key)

    def decay_item(self, key):
        """
            Decays an item in the bag
        :param key:
        :return:
        """
        concept_item = self.peek_using_key(key)
        before = concept_item.get_bag_number()
        NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        concept_item.decay()
        NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self, concept_item)
        after = concept_item.get_bag_number()
        diff = abs(after - before)
        # remove the difference in priority so its less likely to be randomly selected
        idx_to_rmv = bisect(self.items, key)
        for i in range(diff):
            self.items.pop(idx_to_rmv-i-1)

    def peek_max(self):
        """
            Peek an object in the highest priority bucket

            Returns None if Bag is empty
        """
        item = self.ordered_items.extract_max()
        self.take_using_key(item.key)
        return item


    def take_using_key(self, key):
        """
        Take an item from the bag using the key

        :param key: key of the item to remove from the Bag
        :return: the item which was removed from the bucket
        """
        assert (key in self.item_lookup_dict), "Given key does not exist in this bag"

        self.count -=1

        item = self.peek_using_key(key)
        elements_in_bag = item.get_bag_number()

        # remove the difference in priority so its less likely to be randomly selected
        idx_to_rmv = bisect(self.items, key)
        for i in range(elements_in_bag):
            self.items.pop(idx_to_rmv-i-1)

        NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)

        return item

    def _take_min(self):
        """
            :returns the lowest priority item taken from the Bag
        """
        item = self.ordered_items.extract_min()
        self.take_using_key(item.key)
        return item

    def _peek_probabilistically(self):
        """
            Probabilistically selects a priority value / bucket, then peeks an item from that bucket.

            :returns (item, index of item in the current bucket)
        """
        if self.count == 0: return None, None
        rnd = random.random()  # randomly generated number in [0.0, 1.0)
        key = self.items[round(rnd*(len(self.items)-1))]
        return self.item_lookup_dict[key]

