import depq
import Config
import random
import Global
import NALGrammar
import NALSyntax
import NARSMemory

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
    next_item_id = 0
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
        return (hash(object) in self.item_lookup_table or str(object) in self.item_lookup_table)

    def __len__(self):
        return self.count

    def __iter__(self):
        return iter(self.item_lookup_table.values())

    def put_new_item(self, object):
        """
            Insert a new object in the bag - it will be wrapped in an item
            The object/item can be accessed by object's key, which is the object's hash
        """
        assert (isinstance(object, self.item_type)), "object must be of type " + str(self.item_type)
        item = Bag.Item(object,self)
        self.put(item)

    def put(self, item):
        """
            Place an item in the bag
        """
        assert (isinstance(item, Bag.Item)), "item must be of type " + str(Bag.Item)
        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)

        if item.key not in self.item_lookup_table:
            # put item into lookup table and bucket
            self.item_lookup_table[item.key] = item
            self.buckets[item.get_target_bucket_number()].append(item)

            # increase Bag count
            self.count = self.count + 1

            # Print to internal data GUI
            if Global.GlobalGUI.gui_use_internal_data:
                Global.GlobalGUI.print_to_output(msg=str(item), data_structure=self)

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

    def take(self, key=None):
        """
            Remove an item from the bag, either probabilistically or from its key

            Input:
                object - if object is not passed, probabilistically removes it's corresponding item from the bag
                        if object is passed, the item is not removed from the bag
        """
        if self.count == 0:
            return None  # no items

        if key is None:
            return self._take_item_probabilistically()
        return self._take_item_by_key(key)

    def _take_item_by_key(self, key):
        assert (key in self.item_lookup_table), "Given key does not exist in this bag"
        item = self.item_lookup_table.pop(key)  # remove item reference from lookup table
        self.buckets[item.current_bucket_number].remove(item)  # remove item reference from bucket
        self.count = self.count - 1  # decrement bag count

        # GUI
        if Global.GlobalGUI.gui_use_internal_data:
            Global.GlobalGUI.remove_from_output(str(item), data_structure=self)

        return item

    def _take_item_probabilistically(self):
        """
            Probabilistically peeks a priority bucket, then peeks an item from that bucket.
            The peeked item is removed from the bag.
        """
        _, randidx = self._peek_item_probabilistically()
        item = self.buckets[self.current_bucket_number].pop(randidx)
        # remove item reference from lookup table
        self.item_lookup_table.pop(item.key)
        self.count = self.count - 1  # decrement bag count

        # update GUI
        # GUI
        if Global.GlobalGUI.gui_use_internal_data:
            Global.GlobalGUI.remove_from_output(str(item), data_structure=self)

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
        self.item_lookup_table.pop(item.key)
        self.count = self.count - 1  # decrement bag count

        # restore original index
        self.current_bucket_number = oldidx

        # update GUI
        if Global.GlobalGUI.gui_use_internal_data:
            Global.GlobalGUI.remove_from_output(str(item), data_structure=self)

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

    def get_next_item_id(self):
        self.next_item_id = self.next_item_id + 1
        return self.next_item_id - 1

    class Item:
        """
            Item in a bag. Wraps the objects stored in this bag

            Consists of:
                object (e.g. Concept, Task, etc.)

                budget ($priority$)
        """
        def __init__(self, object, containing_bag):
            """

            :param object: object to wrap in the item
            :param containing_bag: the Bag instance that will contain this item
            """
            self.object = object
            self.id = containing_bag.get_next_item_id()
            priority = None
            quality = None
            if isinstance(object, Task):
                if isinstance(object.sentence, NALGrammar.Judgment):
                    priority = object.sentence.value.confidence
                else: # question or goal, give high priority
                    priority = 0.99
                quality = 0.01
                self.key = str(self.id)
            elif isinstance(object, NARSMemory.Concept):
                priority = 0.99
                quality = 0.50
                self.key = str(object.term)

            if priority is not None:
                self.budget = Bag.Item.Budget(priority=priority, quality=quality)
            else:
                #print("Don't know how to handle unknown item added to bag. Using default budget")
                self.key = str(object)
                self.budget = Bag.Item.Budget()

            self.current_bucket_number = self.get_target_bucket_number()

        def __str__(self):
            return Global.Global.BAG_ITEM_ID_MARKER + str(self.id) + Global.Global.ID_END_MARKER + str(self.object) + " " + Global.GlobalGUI.GUI_BUDGET_SYMBOL + "{:.2f}".format(self.budget.priority) + Global.GlobalGUI.GUI_BUDGET_SYMBOL


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
            new_priority = self.budget.priority * Config.BAG_PRIORITY_DECAY_MULTIPLIER
            if new_priority >= self.budget.quality:
                self.budget.priority = new_priority

        class Budget:
            """
                Budget deciding the proportion of the system's time-space resources to allocate to a Bag Item.
                Priority determines how likely an item is to be selected,
                Quality defines the Item's base priority (its lowest possible priority)
            """
            def __init__(self, priority=0.99, quality=0.01):
                self.priority = priority
                self.quality = quality

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

    def __init__(self, punctuation=NALSyntax.Punctuation.Judgment, maxsize=Config.TABLE_CAPACITY):
        self.punctuation = punctuation
        self.depq = depq.DEPQ(iterable=None, maxlen=None)  # maxheap depq
        self.maxsize = maxsize

    def __iter__(self):
        return iter(self.depq)

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

    def __init__(self, sentence, is_input_task=False):
        NALGrammar.assert_sentence(sentence)
        self.sentence = sentence
        self.creation_timestamp: int = Global.Global.NARS.memory.current_cycle_number  # save the task's creation time
        self.is_from_input: bool = is_input_task
        self.needs_initial_processing: bool = True
        #only used for question tasks
        self.needs_to_be_answered_in_output: bool = True

    def __str__(self):
        return self.sentence.get_formatted_string_no_id()



# Asserts
def assert_task(j):
    assert (isinstance(j, Task)), str(j) + " must be a Task"
