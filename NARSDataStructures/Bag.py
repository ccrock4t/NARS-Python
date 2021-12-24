"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import os
import random
import timeit as time
import numpy as np
import Config
import Global
import NARSDataStructures.ItemContainers
from multiprocessing import Pool


class Bag(NARSDataStructures.ItemContainers.ItemContainer):
    """
        Probabilistic priority-queue

        --------------------------------------------

        An array of buckets, where each bucket holds items of a certain priority
        (e.g. 100 buckets, bucket 1 - hold items with 0.01 priority,  bucket 50 - hold items with 0.50 priority)
    """

    def __init__(self, item_type, capacity):
        self.level = 0
        self.buckets = {}  # un-normalized probability weight vector (e.g. item priority)
        self.count = 0
        for i in range(100):
            self.buckets[i] = []
        NARSDataStructures.ItemContainers.ItemContainer.__init__(self, item_type=item_type, capacity=capacity)
        self.highest_populated_bucket = -1

    def __len__(self):
        return len(self.item_lookup_dict)

    def __iter__(self):
        return iter(list(self.item_lookup_dict.values()).__reversed__())

    def clear(self):
        self.__init__(item_type=self.item_type,
                      capacity=self.capacity)

    def put_new(self, object):
        """
            Place a NEW Item into the bag.

            :param Bag Item to place into the Bag
            :returns the new item
        """
        assert (isinstance(object, self.item_type)), "item object must be of type " + str(self.item_type)
        item = NARSDataStructures.ItemContainers.ItemContainer.put_new(self,object)

        bucket = item.budget.get_priority_bucket()
        self.buckets[bucket].append(item)

        # remove lowest priority item if over capacity
        if len(self) > self.capacity:
            purged_item = self._take_min()

        return item

    def peek(self, key=None):
        """
            Peek an object from the bag using its key.
            If key is None, peeks probabilistically

            :returns An item peeked from the Bag; None if item could not be peeked from the Bag
        """
        if len(self) == 0: return None  # no items

        if key is None:
            item = self._peek_probabilistically()
        else:
            item = NARSDataStructures.ItemContainers.ItemContainer.peek_using_key(self, key=key)

        return item

    def change_priority(self, key, new_priority):
        """
            Changes an item priority in the bag
        :param key:
        :return:
        """
        item = self.peek_using_key(key)

        # take from bucket
        current_bucket = item.budget.get_priority_bucket()
        self.buckets[current_bucket].remove(item)

        # change item priority attribute, and GUI if necessary
        item.budget.set_priority(new_priority)

        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self,
                                                                                                           item)
        # add to new bucket
        new_bucket = item.budget.get_priority_bucket()
        self.buckets[new_bucket].append(item)


    def strengthen_item(self, key, multiplier=Config.PRIORITY_STRENGTHEN_VALUE):
        """
            Decays an item in the bag
        :param key:
        :return:
        """
        item = self.peek_using_key(key)

        # take from bucket
        current_bucket = item.budget.get_priority_bucket()
        self.buckets[current_bucket].remove(item)

        # change item priority attribute, and GUI if necessary
        item.strengthen(multiplier=multiplier)

        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self,
                                                                                                           item)
        # add to new bucket
        new_bucket = item.budget.get_priority_bucket()
        self.buckets[new_bucket].append(item)


    def decay_item(self, key):
        """
            Decays an item in the bag
        :param key:
        :return:
        """
        item = self.peek_using_key(key)

        # take from bucket
        current_bucket = item.budget.get_priority_bucket()
        self.buckets[current_bucket].remove(item)

        # change item priority attribute, and GUI if necessary
        item.decay()

        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self,
                                                                                                           item)

        # add to new bucket
        new_bucket = item.budget.get_priority_bucket()
        self.buckets[new_bucket].append(item)

    def take_using_key(self, key):
        """
        Take an item from the bag using the key

        :param key: key of the item to remove from the Bag
        :return: the item which was removed from the bucket
        """
        assert (key in self.item_lookup_dict), "Given key does not exist in this bag"
        item = NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
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
        if len(self) == 0: return None, None
        while True:
            # if rolled higher than the current bucket, keep looking
            self.level = (self.level + 1) % 100
            level_bucket = self.buckets[self.level]
            if len(level_bucket) == 0: continue

            # go into bucket, based on priority
            rnd = random.randint(0, 100)
            if rnd <= self.level:
                # use this bucket
                break


        rnd_idx = random.randint(0,len(level_bucket)-1)
        item = level_bucket[rnd_idx]
        return item
