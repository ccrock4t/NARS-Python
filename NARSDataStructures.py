import Config
import random

import Global
import NALInferenceRules

from NALGrammar import assert_sentence
"""
    Author: Christian Hahm
    Created: December 24, 2020
"""
class Bag:
    """
        Probabilistic priority-queue

        --------------------------------------------

        An array of buckets, where each bucket holds items of a certain priority
        (e.g. 100 buckets, bucket 1 - hold items with 0.01 priority,  bucket 50 - hold items with 0.50 priority)
    """
    def __init__(self, item_type):
        self.item_type = item_type # the class of the objects  this bag stores (be wrapped in Item)

        self.capacity = Config.BAG_CAPACITY # maximum number of items that can be stored in this bag
        self.number_of_buckets = Config.BAG_NUMBER_OF_BUCKETS # number of buckets in the bag (the bag's granularity)
        self.item_lookup_table = dict() # for accessing item by key
        self.buckets = dict() # for accessing items by priority

        self.current_bucket_number = 0 # keeps track of the Bag's current bucket number
        self.count = 0

        for i in range(0, self.number_of_buckets):
            self.buckets[i] = []

    def put_new_item_from_object(self, object):
        """
            Convert an object into an item and place the item in the bag
        """
        assert (isinstance(object, self.item_type)), "object must be of type " + str(self.item_type)
        if hash(object) not in self.item_lookup_table:
            # create item
            item = Bag.Item(object)
            #put into lookup table and bucket
            self.item_lookup_table[hash(object)] = item
            self.buckets[item.get_new_bucket_number()].append(item)
            self.count = self.count + 1


    def put(self, item):
        """
            Place an item in the bag
        """
        assert (isinstance(item, Bag.Item)), "item must be of type " + str(Bag.Item)
        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)
        if hash(item.object) not in self.item_lookup_table:
            # put item into lookup table and bucket
            self.item_lookup_table[hash(item.object)] = item
            self.buckets[item.get_new_bucket_number()].append(item)

            self.count = self.count + 1

    def get(self, object):
        """
            Get an item from the bag from its object

            Returns None if the object isn't in the bag
        """
        if hash(object) in self.item_lookup_table:
            return self.item_lookup_table[hash(object)]
        return None

    def take(self, object=None):
        """
            Remove an item from the bag, either probabilistically or from its object

            Input:
                object - if object is not passed, probabilistically removes it's corresponding item from the bag
                        if object is passed, the item is not removed from the bag
        """
        if self.count == 0:
            return None # no items

        if object is None:
            return self.take_item_probabilistically()
        return self.take_item_by_key(hash(object))

    def take_item_by_key(self, key):
        assert(key in self.item_lookup_table), "Given key does not exist in this bag"
        item = self.item_lookup_table.pop(key) # remove item reference from lookup table
        self.buckets[item.current_bucket_number].remove(item) # remove item reference from bucket
        self.count = self.count - 1 # decrement bag count
        return item

    def take_item_probabilistically(self):
        """
            Probabilistically selects a priority value / bucket, then removes an item from that bucket.
        """
        self.move_to_next_nonempty_bucket()  # try next non-empty bucket
        rnd = random.random()  # randomly generated number in [0.0, 1.0)

        # select the current bucket only if rnd is smaller than
        # the ratio of the bucket number to total number of buckets
        # (e.g. the first bucket will never be selected (0% priority),
        # the last bucket is guaranteed to be selected (100% priority))
        while rnd >= (self.current_bucket_number / (self.number_of_buckets - 1)):
            self.move_to_next_nonempty_bucket() # try next non-empty bucket
            rnd = random.random()  # randomly generated number in [0.0, 1.0)

        # pop random item from currently selected bucket
        rnd = random.random()  # randomly generated number in [0.0, 1.0)
        maxidx = len(self.buckets[self.current_bucket_number]) - 1
        randidx = int(round(rnd * maxidx))
        item = self.buckets[self.current_bucket_number].pop(randidx)
        # remove item reference from lookup table
        self.item_lookup_table.pop(hash(item.object))
        self.count = self.count - 1 # decrement bag count

        return item

    def move_to_next_nonempty_bucket(self):
        """
            Select the next non-empty bucket after the currently selected bucket
        """
        self.move_to_next_bucket()
        while len(self.buckets[self.current_bucket_number]) == 0:
            self.move_to_next_bucket()

    def move_to_next_bucket(self):
        """
            Select the next bucket after the currently selected bucket
        """
        self.current_bucket_number = (self.current_bucket_number + 1) % self.number_of_buckets

    class Item:
        """
            Item in a bag. Wraps the objects stored in this bag

            Consists of:
                object (e.g. Concept, Task, etc.)

                budget ($priority;durability;quality$)
        """
        def __init__(self, object):
            self.object = object
            self.budget = Bag.Item.Budget(priority=0.9, durability=0.9, quality=0.9)
            self.current_bucket_number = self.get_new_bucket_number()

        def get_new_bucket_number(self):
            """
                Output: The bucket number this item belongs in.
                It is calculated as this item's priority rounded to 2 decimals * 100 (as an int)
            """
            return int(round(self.budget.priority, 2) * 100)

        class Budget:
            def __init__(self, priority=0.0, durability=0.0, quality=0.0):
                self.priority = priority
                self.durability = durability
                self.quality = quality

            def increase_priority(self, v):
                self.durability = min(1.0, NALInferenceRules.bor(self.priority, v))

            def decrease_priority(self, v):
                self.durability = NALInferenceRules.band(self.priority, v)

            def increase_durability(self, v):
                new_durability = NALInferenceRules.bor(self.durability, v)
                if new_durability >= 1.0:
                    new_durability = 1.0 - Config.TRUTH_EPSILON
                self.durability = new_durability

            def decrease_durability(self, v):
                self.durability = NALInferenceRules.band(self.durability, v)


class Buffer:
    """
        Time-restricted Bag
        todo: implement Buffer
    """
    def __init__(self):
        self.capacity = Config.BAG_CAPACITY

class Task:
    """
       NARS Task
    """
    def __init__(self, sentence):
        assert_sentence(sentence)
        self.sentence = sentence
        self.timestamp = Global.current_cycle_number

    def __hash__(self):
        return self.timestamp

    def __str__(self):
        return self.sentence.statement.term.get_formatted_string() + " " + str(self.timestamp)

# Asserts
def assert_task(j):
    assert(isinstance(j, Task)), str(j) + " must be a Task"
