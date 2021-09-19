"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import heapq
import random
from bisect import bisect

import numpy as np

import Config
import NARSDataStructures.ItemContainers

class Bag(NARSDataStructures.ItemContainers.ItemContainer):
    """
        Probabilistic priority-queue

        --------------------------------------------

        An array of buckets, where each bucket holds items of a certain priority
        (e.g. 100 buckets, bucket 1 - hold items with 0.01 priority,  bucket 50 - hold items with 0.50 priority)
    """

    def __init__(self, item_type, capacity):
        self.item_keys = np.array([]) # items contained in the bag
        self.weights = np.array([]) # un-normalized probability weight vector (e.g. item priority)
        self.weights_sum = 0
        self.item_key_to_index = {} # get item index from key
        self.ordered_items = NARSDataStructures.Other.Depq() # for taking min and max
        NARSDataStructures.ItemContainers.ItemContainer.__init__(self, item_type=item_type,capacity=capacity)

    def __len__(self):
        return len(self.item_keys)

    def __iter__(self):
        return iter(list(self.item_lookup_dict.values()).__reversed__())

    def put(self, item):
        """
            Place a NEW Item into the bag.

            :param Bag Item to place into the Bag
            :returns the new item
        """
        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)

        NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self, item)  # Item Container


        self.item_keys = np.append(self.item_keys, item.key) # insert at last index
        weight = item.budget.get_priority_weight()
        self.weights = np.append(self.weights,weight)  # insert at last index
        self.weights_sum += weight
        priority = item.budget.get_priority()
        self.ordered_items.insert_object(item, priority)  # insert into ordered queue
        self.item_key_to_index[item.key] = len(self.item_keys) - 1 # last index

        # remove lowest priority item if over capacity
        purged_item = None
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
            item = NARSDataStructures.ItemContainers.ItemContainer.peek_using_key(self,key=key)

        return item

    def change_priority(self, key, new_priority):
        """
            Changes an item priority in the bag
        :param key:
        :return:
        """
        concept_item = self.peek_using_key(key)

        # subtract current weight from sum
        current_weight = concept_item.budget.get_priority_weight()
        self.weights_sum -= current_weight

        # change item priority attribute, and GUI if necessary
        concept_item.budget.set_priority(new_priority)

        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self, concept_item)

        # insert new weight
        new_weight = concept_item.budget.get_priority_weight()
        item_index = self.item_key_to_index[key]
        self.weights[item_index] = new_weight
        self.weights_sum += new_weight


    def strengthen_item(self, key):
        """
            Decays an item in the bag
        :param key:
        :return:
        """
        concept_item = self.peek_using_key(key)

        # subtract current weight from sum
        current_weight = concept_item.budget.get_priority_weight()
        self.weights_sum -= current_weight

        # change item priority attribute, and GUI if necessary
        concept_item.strengthen()

        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self, concept_item)

        # insert new weight
        new_weight = concept_item.budget.get_priority_weight()
        item_index = self.item_key_to_index[key]
        self.weights[item_index] = new_weight
        self.weights_sum += new_weight

    def decay_item(self, key):
        """
            Decays an item in the bag
        :param key:
        :return:
        """
        concept_item = self.peek_using_key(key)

        # subtract current weight from sum
        current_weight = concept_item.budget.get_priority_weight()
        self.weights_sum -= current_weight

        # change item priority attribute, and GUI if necessary
        concept_item.decay()

        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)
        if Config.GUI_USE_INTERFACE: NARSDataStructures.ItemContainers.ItemContainer._put_into_lookup_dict(self, concept_item)

        # insert new weight
        new_weight = concept_item.budget.get_priority_weight()
        item_index = self.item_key_to_index[key]
        self.weights[item_index] = new_weight
        self.weights_sum += new_weight


    def peek_max(self):
        """
            Peek an object in the highest priority bucket

            Returns None if Bag is empty
        """
        item = self.ordered_items.peek_max()
        return item

    def take_using_key(self, key):
        """
        Take an item from the bag using the key

        :param key: key of the item to remove from the Bag
        :return: the item which was removed from the bucket
        """
        assert (key in self.item_lookup_dict), "Given key does not exist in this bag"

        item_idx = self.item_key_to_index[key]

        item = NARSDataStructures.ItemContainers.ItemContainer._take_from_lookup_dict(self, key)

        self.item_keys = np.delete(self.item_keys,item_idx)
        self.weights = np.delete(self.weights, item_idx)
        self.weights_sum -= item.budget.get_priority_weight()

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
        normalized_weights = self.weights / self.weights_sum
        try:
            key = np.random.choice(self.item_keys, p=normalized_weights)
        except:
            assert False, "ERROR: " + str(self.weights_sum) + " and " + str(np.sum(self.weights)) + " with len " + str(
                len(self.item_keys)) + " and len " + str(len(self.weights))
        return self.item_lookup_dict[key]

