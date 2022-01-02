"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import ctypes
import math
import random

import sortedcontainers

import Config
import NARSDataStructures.ItemContainers
import NALInferenceRules


class Bag(NARSDataStructures.ItemContainers.ItemContainer):
    """
        Probabilistic priority-queue

        --------------------------------------------

        An array of buckets, where each bucket holds items of a certain priority
        (e.g. 100 buckets, bucket 1 - hold items with 0.01 priority,  bucket 50 - hold items with 0.50 priority)
    """

    def __init__(self, item_type, capacity, granularity=Config.BAG_GRANULARITY):
        self.level = 0
        self.buckets = {}
        for i in range(granularity):
            self.buckets[i] = None
        NARSDataStructures.ItemContainers.ItemContainer.__init__(self, item_type=item_type, capacity=capacity)

    def __len__(self):
        return len(self.item_lookup_dict)

    def __iter__(self):
        return iter(list(self.item_lookup_dict.values()).__reversed__())

    def clear(self):
        self.level = 0
        for i in range(len(self.buckets)):
            self.buckets[i] = None
        NARSDataStructures.ItemContainers.ItemContainer._clear(self)

    def put_new(self, object):
        """
            Place a NEW Item into the bag.

            :param Bag Item to place into the Bag
            :returns the new item
        """
        assert (isinstance(object, self.item_type)), "item object must be of type " + str(self.item_type)
        item = NARSDataStructures.ItemContainers.ItemContainer.put_new(self,object)

        # remove lowest priority item if over capacity
        if len(self) > self.capacity:
            purged_item = self._take_min()

        self.add_item_to_bucket(item)

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

        self.remove_item_from_bucket(item=item)

        # change item priority attribute, and GUI if necessary
        item.budget.set_priority(new_priority)

        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self,
                                                                                                           item)
        # add to new bucket
        self.add_item_to_bucket(item=item)

    def add_item_to_bucket(self,item):
        # add to appropriate bucket
        bucket_num = self.calc_bucket_num_from_priority(item.budget.get_priority())
        if self.buckets[bucket_num] is None: self.buckets[bucket_num] = sortedcontainers.SortedList()
        bucket = self.buckets[bucket_num]
        bucket.add(id(item))
        item.bucket_num = bucket_num

    def remove_item_from_bucket(self,item):
        # take from bucket
        bucket = self.buckets[item.bucket_num]
        bucket.remove(id(item))
        item.bucket_num = None


    def strengthen_item(self, key, multiplier=Config.PRIORITY_STRENGTHEN_VALUE):
        """
            Decays an item in the bag
        :param key:
        :return:
        """
        item = self.peek_using_key(key)
        # change item priority attribute, and GUI if necessary
        new_priority = NALInferenceRules.ExtendedBooleanOperators.bor(item.budget.get_priority(), multiplier)
        self.change_priority(key, new_priority=new_priority)


    def decay_item(self, key, multiplier=Config.PRIORITY_DECAY_VALUE):
        """
            Decays an item in the bag
        :param key:
        :return:
        """
        item = self.peek_using_key(key)
        new_priority = NALInferenceRules.ExtendedBooleanOperators.band(item.budget.get_priority(), multiplier)
        self.change_priority(key, new_priority=new_priority)

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
        #todo buckets
        print('Taking Min')
        item = None
        try:
            item = self.ordered_items.extract_min()
            self.take_using_key(item.key)
        except:
            pass
        return item


    def _peek_probabilistically(self):
        """
            Probabilistically selects a priority value / bucket, then peeks an item from that bucket.

            :returns (item, index of item in the current bucket)
        """
        if len(self) == 0: return None, None
        self.level = random.randint(0, len(self.buckets)- 1)
        while True:
            level_bucket = self.buckets[self.level]
            if level_bucket is None or len(level_bucket) == 0:
                self.level = (self.level + 1) % len(self.buckets)
                continue

            # try to go into bucket
            rnd = random.randint(0,len(self.buckets)-1)

            threshold = self.level
            if rnd <= threshold:
                # use this bucket
                break
            else:
                self.level = (self.level + 1) % len(self.buckets)

        rnd_idx = random.randint(0,len(level_bucket)-1)
        item_id = level_bucket[rnd_idx]
        item = ctypes.cast(item_id, ctypes.py_object).value
        return item

    def calc_bucket_num_from_priority(self, priority):
        return math.floor(priority * len(self.buckets))