from depq import DEPQ
import Config
import random
from Global import GlobalGUI, Global
import NALInferenceRules
import NALGrammar

"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""


class Bag:
    """
        Probabilistic priority-queue

        --------------------------------------------

        An array of buckets, where each bucket holds items of a certain priority
        (e.g. 100 buckets, bucket 1 - hold items with 0.01 priority,  bucket 50 - hold items with 0.50 priority)
    """
    def __init__(self, item_type):
        self.item_type = item_type  # the class of the objects  this bag stores (be wrapped in Item)

        self.capacity = Config.BAG_CAPACITY  # maximum number of items that can be stored in this bag
        self.number_of_buckets = Config.BAG_NUMBER_OF_BUCKETS  # number of buckets in the bag (the bag's granularity)
        self.item_lookup_table = dict()  # for accessing item by key
        self.buckets = dict()  # for accessing items by priority

        self.current_bucket_number = 0  # keeps track of the Bag's current bucket number
        self.count = 0  # number of items in the bag

        # initialize buckets
        for i in range(1, self.number_of_buckets + 1):
            self.buckets[i] = []

    def __contains__(self, object):
        return (hash(object) in self.item_lookup_table)

    def put_new_item(self, object):
        """
            Insert a new object in the bag - it will be wrapped in an item
            The object/item can be accessed by object's key, which is the hash of its string representation.
        """
        assert (isinstance(object, self.item_type)), "object must be of type " + str(self.item_type)
        item = Bag.Item(object)
        self.put(item)

    def put(self, item):
        """
            Place an item in the bag
        """
        assert (isinstance(item, Bag.Item)), "item must be of type " + str(Bag.Item)
        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)

        key = hash(item.object)
        if key not in self.item_lookup_table:
            # put item into lookup table and bucket
            self.item_lookup_table[key] = item
            self.buckets[item.get_target_bucket_number()].append(item)

            # increase Bag count
            self.count = self.count + 1

            # Print to internal data GUI
            if GlobalGUI.gui_use_internal_data:
                GlobalGUI.print_to_output(msg=str(item), data_structure=self)

            # remove lowest priority item if over capacity
            if self.count > self.capacity:
                self._take_smallest_priority_item()

    def peek(self, key=None):
        """
            Peek an item from the bag using its key.
            If key is None, peeks probabilistically

            Returns None if the object isn't in the bag
        """
        if self.count == 0:
            return None  # no items

        item = None
        if key is None:
            item, _ = self._peek_item_probabilistically()
        else:
            if key in self.item_lookup_table:
                item = self.item_lookup_table[key]
        return item

    def take(self, object=None):
        """
            Remove an item from the bag, either probabilistically or from its object

            Input:
                object - if object is not passed, probabilistically removes it's corresponding item from the bag
                        if object is passed, the item is not removed from the bag
        """
        if self.count == 0:
            return None  # no items

        if object is None:
            return self._take_item_probabilistically()
        return self._take_item_by_key(hash(object))

    def _take_item_by_key(self, key):
        assert (key in self.item_lookup_table), "Given key does not exist in this bag"
        item = self.item_lookup_table.pop(key)  # remove item reference from lookup table
        self.buckets[item.current_bucket_number].remove(item)  # remove item reference from bucket
        self.count = self.count - 1  # decrement bag count

        # GUI
        if GlobalGUI.gui_use_internal_data:
            GlobalGUI.remove_from_output(str(item), data_structure=self)

        return item

    def _take_item_probabilistically(self):
        """
            Probabilistically peeks a priority bucket, then peeks an item from that bucket.
            The peeked item is removed from the bag.
        """
        _, randidx = self._peek_item_probabilistically()
        item = self.buckets[self.current_bucket_number].pop(randidx)
        # remove item reference from lookup table
        self.item_lookup_table.pop(hash(item.object))
        self.count = self.count - 1  # decrement bag count

        # update GUI
        # GUI
        if GlobalGUI.gui_use_internal_data:
            GlobalGUI.remove_from_output(str(item), data_structure=self)

        return item

    def _take_smallest_priority_item(self):
        """
            Selects the lowest priority bucket, and removes an item from it.
        """
        # store old index so we can restore it
        oldidx = self.current_bucket_number

        # move to lowest non-empty priority bucket
        self.current_bucket_number = 0
        self._move_to_next_nonempty_bucket()

        # peek a random item from the bucket
        _, randidx = self._peek_random_item_from_current_bucket()

        # remove the item
        item = self.buckets[self.current_bucket_number].pop(randidx)
        # remove item reference from lookup table
        self.item_lookup_table.pop(hash(item.object))
        self.count = self.count - 1  # decrement bag count

        # restore original index
        self.current_bucket_number = oldidx

        # update GUI
        if GlobalGUI.gui_use_internal_data:
            GlobalGUI.remove_from_output(str(item), data_structure=self)

        return item

    def _peek_item_probabilistically(self):
        """
            Probabilistically selects a priority value / bucket, then peeks an item from that bucket.

            Returns: item, index of item in current bucket
        """

        # probabilistically select a priority bucket
        self._move_to_next_nonempty_bucket()  # try next non-empty bucket
        rnd = random.random()  # randomly generated number in [0.0, 1.0)
        bucket_probability = self.current_bucket_number / self.number_of_buckets

        while rnd >= bucket_probability:
            # bucket was not selected, try next bucket
            self._move_to_next_nonempty_bucket()  # try next non-empty bucket
            rnd = random.random()  # randomly generated number in [0.0, 1.0)

        # peek a random item from the bucket
        item, randidx = self._peek_random_item_from_current_bucket()

        return item, randidx

    def _peek_random_item_from_current_bucket(self):
        """
            Picks an item from the current bucket using uniform randomness.
            Returns: item, index of item in current bucket
        """
        # pop random item from currently selected bucket
        rnd = random.random()  # another randomly generated number in [0.0, 1.0)
        maxidx = len(self.buckets[self.current_bucket_number]) - 1
        randidx = int(round(rnd * maxidx))
        item = self.buckets[self.current_bucket_number][randidx]
        return item, randidx

    def _move_to_next_nonempty_bucket(self):
        """
            Select the next non-empty bucket after the currently selected bucket
        """
        self._move_to_next_bucket()
        while len(self.buckets[self.current_bucket_number]) == 0:
            self._move_to_next_bucket()

    def _move_to_next_bucket(self):
        """
            Select the next bucket after the currently selected bucket
        """
        self.current_bucket_number = (self.current_bucket_number % self.number_of_buckets) + 1

    class Item:
        """
            Item in a bag. Wraps the objects stored in this bag

            Consists of:
                object (e.g. Concept, Task, etc.)

                budget ($priority;durability;quality$)
        """

        def __init__(self, object):
            self.object = object
            # todo implement priority
            self.budget = Bag.Item.Budget(priority=0.9, durability=0.9, quality=0.9)
            self.current_bucket_number = self.get_target_bucket_number()

        def __str__(self):
            return str(self.object) + " " + GlobalGUI.GUI_PRIORITY_SYMBOL + "{:.2f}".format(self.budget.priority) + GlobalGUI.GUI_PRIORITY_SYMBOL

        def get_target_bucket_number(self):
            """
                Returns: The bucket number this item belongs in according to its priority.

                It is calculated as this item's priority [0,1] converted to a corresponding probability
                based on Bag granularity
                (e.g. Priority=0.5, 100 buckets -> bucket 50, 200 buckets -> bucket 100, 50 buckets -> bucket 25)
            """
            return int(round(self.budget.priority, 2) * 100) * Config.BAG_NUMBER_OF_BUCKETS / 100

        def decay(self):
            """
                Decay this item's priority
            """
            if self.budget.priority > 0.05:
                self.budget.priority = self.budget.priority * Config.BAG_PRIORITY_DECAY_MULTIPLIER

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


class Table:
    """
        NARS Table, stored within Concepts.
        Tables store Narsese sentences using a double ended priority queue, sorted by confidence
        It purges lowest-confidence items when it overflows.
    """

    def __init__(self, punctuation=NALGrammar.Punctuation.Judgment, maxsize=Config.TABLE_CAPACITY):
        self.punctuation = punctuation
        self.depq = DEPQ(iterable=None, maxlen=None)  # maxheap depq
        self.maxsize = maxsize

    def insert(self, sentence):
        """
            Insert a Sentence into the depq, sorted by confidence.
        """
        assert (
                sentence.punctuation == self.punctuation), "Cannot insert sentence into a Table of different punctuation"
        self.depq.insert(sentence, sentence.value.confidence)
        if (len(self.depq) > self.maxsize):
            self.extract_min()

    def take(self):
        """
            Remove and return the sentence in the table with the highest confidence

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        return self.extract_max()

    def peek(self):
        """
            Peek sentence with highest confidence from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        return self.peek_max()

    def extract_max(self):
        """
            Extract sentence with highest confidence from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        return self.depq.popfirst()[0]

    def extract_min(self):
        """
            Extract sentence with lowest confidence from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        return self.depq.poplast()[0]

    def peek_max(self):
        """
            Peek sentence with highest confidence from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        return self.depq.first()

    def peek_min(self):
        """
            Peek sentence with lowest confidence from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        return self.depq.last()

    def __len__(self):
        return len(self.depq)


class Task:
    """
       NARS Task
    """

    def __init__(self, sentence: NALGrammar.Sentence, is_input_task=False):
        NALGrammar.assert_sentence(sentence)
        self.sentence = sentence
        self.creation_timestamp: int = Global.current_cycle_number  # save the task's creation time
        self.is_from_input: bool = is_input_task
        self.needs_initial_processing: bool = True
        self.interacted_beliefs = []  # list of beliefs this task has already interacted with

        #only used for question tasks
        self.needs_answer_output: bool = True

    def __hash__(self):
        return self.sentence.stamp.id

    def __str__(self):
        return self.sentence.get_formatted_string()


# Asserts
def assert_task(j):
    assert (isinstance(j, Task)), str(j) + " must be a Task"
