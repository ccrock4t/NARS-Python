"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import math
import random

import sortedcontainers

import Config
import NARSDataStructures.ItemContainers

import NARSDataStructures.Other
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
        self.priority_buckets = {}
        self.quality_buckets = {} # store by inverted quality for deletion
        self.granularity = granularity
        for i in range(granularity):
            self.priority_buckets[i] = None
            self.quality_buckets[i] = None
        NARSDataStructures.ItemContainers.ItemContainer.__init__(self, item_type=item_type, capacity=capacity)

    def __len__(self):
        return len(self.item_lookup_dict)

    def __iter__(self):
        return iter(list(self.item_lookup_dict.values()).__reversed__())

    def clear(self):
        self.level = 0
        for i in range(self.granularity):
            self.priority_buckets[i] = None
            self.quality_buckets[i] = None
        NARSDataStructures.ItemContainers.ItemContainer._clear(self)

    def PUT_NEW(self, object):
        """
            Place a NEW Item into the bag.

            :param Bag Item to place into the Bag
            :returns the new item
        """
        assert (isinstance(object, self.item_type)), "item object must be of type " + str(self.item_type)

        # remove lowest priority item if over capacity
        if len(self) == self.capacity:
            purged_item = self._TAKE_MIN()

        # add new item
        item = NARSDataStructures.ItemContainers.ItemContainer.PUT_NEW(self, object)
        self.add_item_to_bucket(item)
        self.add_item_to_quality_bucket(item)

        return item

    def peek(self, key=None):
        """
            Peek an object from the bag using its key.
            If key is None, peeks probabilistically

            :returns An item peeked from the Bag; None if item could not be peeked from the Bag
        """
        if len(self) == 0: return None  # no items

        if key is None:
            item = self._peek_probabilistically(buckets=self.priority_buckets)
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

        self.remove_item_from_its_bucket(item=item)

        # change item priority attribute, and GUI if necessary
        item.budget.set_priority(new_priority)

        # if Config.GUI_USE_INTERFACE:
        #     NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        #     NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self,item)
        # add to new bucket
        self.add_item_to_bucket(item=item)


    def change_quality(self, key, new_quality):
        item = self.peek_using_key(key)

        # remove from sorted
        self.remove_item_from_its_quality_bucket(item)

        # change item quality
        item.budget.set_quality(new_quality)

        # if Config.GUI_USE_INTERFACE:
        #     NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        #     NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self, item)

        # add back to sorted
        self.add_item_to_quality_bucket(item=item)


    def add_item_to_bucket(self,item):
        # add to appropriate bucket
        bucket_num = self.calc_bucket_num_from_value(item.budget.get_priority())
        if self.priority_buckets[bucket_num] is None:
            self.priority_buckets[bucket_num] = sortedcontainers.SortedList()
        bucket = self.priority_buckets[bucket_num]
        bucket.add((id(item),item)) # convert to ID so
        item.bucket_num = bucket_num


    def remove_item_from_its_bucket(self, item):
        # take from bucket
        bucket = self.priority_buckets[item.bucket_num]
        bucket.remove((id(item),item))
        if len(bucket) == 0:
            self.priority_buckets[item.bucket_num] = None
        item.bucket_num = None

    def add_item_to_quality_bucket(self, item):
        # add to appropriate bucket
        bucket_num = self.calc_bucket_num_from_value(1-item.budget.get_quality()) # higher quality should have lower probability of being selected for deletion
        if self.quality_buckets[bucket_num] is None: self.quality_buckets[bucket_num] = sortedcontainers.SortedList()
        bucket = self.quality_buckets[bucket_num]
        bucket.add((id(item),item))
        item.quality_bucket_num = bucket_num

    def remove_item_from_its_quality_bucket(self, item):
        # take from bucket
        bucket = self.quality_buckets[item.quality_bucket_num]
        bucket.remove((id(item),item))
        if len(bucket) == 0:
            self.quality_buckets[item.quality_bucket_num] = None
        item.quality_bucket_num = None

    def strengthen_item_priority(self, key, multiplier=Config.PRIORITY_STRENGTHEN_VALUE):
        """
            Strenghtens an item in the bag
        :param key:
        :return:
        """
        item = self.peek_using_key(key)
        # change item priority attribute, and GUI if necessary
        new_priority = NALInferenceRules.ExtendedBooleanOperators.bor(item.budget.get_priority(), multiplier)
        self.change_priority(key, new_priority=new_priority)


    def strengthen_item_quality(self, key):
        """
            Decays an item in the bag
        :param key:
        :return:
        """
        item = self.peek_using_key(key)
        # change item priority attribute, and GUI if necessary
        new_quality = NALInferenceRules.ExtendedBooleanOperators.bor(item.budget.get_quality(), 0.1)
        self.change_quality(key, new_quality=new_quality)



    def decay_item(self, key, multiplier=Config.PRIORITY_DECAY_VALUE):
        """
            Decays an item in the bag
        :param key:
        :return:
        """
        item = self.peek_using_key(key)
        new_priority = NALInferenceRules.ExtendedBooleanOperators.band(item.budget.get_priority(), multiplier)
        self.change_priority(key, new_priority=new_priority)

    def TAKE_USING_KEY(self, key):
        """
        Take an item from the bag using the key

        :param key: key of the item to remove from the Bag
        :return: the item which was removed from the bucket
        """
        assert (key in self.item_lookup_dict), "Given key does not exist in this bag"
        item = NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        self.remove_item_from_its_bucket(item=item)
        self.remove_item_from_its_quality_bucket(item)
        return item


    def _TAKE_MIN(self):
        """
            :returns the lowest quality item taken from the Bag
        """
        try:
            item = self._peek_probabilistically(buckets=self.quality_buckets)
            assert (item.key in self.item_lookup_dict), "Given key does not exist in this bag"
            item = NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, item.key)
            self.remove_item_from_its_bucket(item=item)
            self.remove_item_from_its_quality_bucket(item)
        except:
            item = None
        return item


    def _peek_probabilistically(self, buckets):
        """
            Probabilistically selects a priority value / bucket, then peeks an item from that bucket.

            :returns item
        """
        if len(self) == 0: return None
        self.level = random.randint(0, self.granularity - 1)

        num_attempts: int = 0
        while True and num_attempts < 100:
            level_bucket = buckets[self.level]
            if level_bucket is None or len(level_bucket) == 0:
                self.level = (self.level + 1) % self.granularity
                continue

            # try to go into bucket
            rnd = random.randint(0, self.granularity - 1)

            threshold = self.level
            if rnd <= threshold:
                # use this bucket
                break
            else:
                self.level = (self.level + 1) % self.granularity

            num_attempts += 1

        if num_attempts >= 100: return None

        rnd_idx = random.randint(0,len(level_bucket)-1)
        _, item = level_bucket[rnd_idx]

        return item

    def calc_bucket_num_from_value(self, val):
        return min(math.floor(val * self.granularity), self.granularity - 1)