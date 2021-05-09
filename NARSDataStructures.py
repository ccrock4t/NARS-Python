import queue

import depq
import Config
import random
import Global
import NALGrammar
import NARSGUI
import NARSMemory

"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""

class ItemContainer:
    """
        Base Class for data structures which contain "Items", as defined in this class.

        Examples of Item Containers include Bag and Buffer.
    """
    def __init__(self, item_type, capacity):
        self.item_type = item_type  # the class of the objects this Container stores (be wrapped in Item)
        self.item_lookup_dict = dict()  # for accessing Item by key
        self.next_item_id = 0
        self.capacity = capacity

    def __contains__(self, object):
        """
            Purpose:
                Check if the object is contained in the Bag by checking whether its key is in the item lookup table

        :param object: object to look for in the Bag
        :return: True if the item is in the Bag;
                    False otherwise
        """
        return ItemContainer.Item.get_key_from_object(object) in self.item_lookup_dict

    def __iter__(self):
        return iter(self.item_lookup_dict.values())

    def _put_into_lookup_dict(self, item):
        """
            Puts item into lookup table and GUI
            :param item: put an Item into the lookup dictionary.
        """
        # put item into lookup table
        self.item_lookup_dict[item.key] = item

        if Global.Global.gui_use_internal_data:
            NARSGUI.NARSGUI.print_to_output(str(item), data_structure=self)

    def _take_from_lookup_dict(self, key):
        """
            Removes an Item from the lookup dictionary using its key,
            and returns the Item.

        :param key: Key of the Item to remove.
        :return: The Item that was removed.
        """
        item = self.item_lookup_dict.pop(key)  # remove item reference from lookup table

        if Global.Global.gui_use_internal_data:
            NARSGUI.NARSGUI.remove_from_output(str(item), data_structure=self)

        return item

    def put_new(self, object):
        item = ItemContainer.Item(object, self.get_next_item_id())
        return self.put(item)

    def _take_min(self):
        assert False,"Take smallest priority item not defined for generic Item Container!"

    def get_next_item_id(self) -> int:
        self.next_item_id += 1
        return self.next_item_id - 1

    def peek_using_key(self,key=None):
        """
            Peek an Item using its key

            :param key: Key of the item to peek
            :return: Item peeked from the data structure
        """
        assert key is not None, "Key cannot be none when peeking with a key!"
        if key not in self.item_lookup_dict: return None
        return self.item_lookup_dict[key]

    class Item:
        """
            Item in an Item Container. Wraps an object.

            Consists of:
                object (e.g. Concept, Task, etc.)

                budget ($priority$)
        """
        def __init__(self, object, id):
            """
            :param object: object to wrap in the item
            :param container: the Item Container instance that will contain this item
            """
            self.object = object
            self.id = id
            priority = None
            quality = None
            if isinstance(object, Task):
                if isinstance( object.sentence, NALGrammar.Judgment):
                    priority = object.sentence.value.confidence
                else:
                    priority = 0.95
                quality = 0.010
            elif isinstance(object, NARSMemory.Concept):
                priority = 0.990 / object.term.syntactic_complexity
                quality = 0.500
            elif isinstance(object, NALGrammar.Sentence):
                priority = object.value.confidence
                quality = 0.500

            if priority is not None:
                self.key = ItemContainer.Item.get_key_from_object(object)
                self.budget = ItemContainer.Item.Budget(priority=priority, quality=quality)
            else:
                self.key = str(object)
                self.budget = ItemContainer.Item.Budget()

            self.current_bucket_number = self.get_target_bucket_number()

        @classmethod
        def get_key_from_object(cls, object):
            """
                :param object:
                :return: key for object
            """
            key = None
            if isinstance(object, Task):
                key = str(object.sentence.stamp.id)
            elif isinstance(object, NARSMemory.Concept):
                key = str(object.term)
            elif isinstance(object, NALGrammar.Sentence):
                key = str(object.stamp.id)
            else:
                key = str(object)
            return key

        def __str__(self):
            return Global.Global.MARKER_ITEM_ID \
                   + str(self.id) + Global.Global.MARKER_ID_END \
                   + str(self.object) \
                   + " " \
                   + NARSGUI.NARSGUI.GUI_BUDGET_SYMBOL \
                   + "{:.3f}".format(self.budget.priority) \
                   + NARSGUI.NARSGUI.GUI_BUDGET_SYMBOL


        def get_target_bucket_number(self):
            """
                Returns: The Bag bucket number this item belongs in according to its priority.

                It is calculated as this item's priority [0,1] converted to a corresponding probability
                based on Bag granularity
                (e.g. Priority=0.5, 100 buckets -> bucket 50, 200 buckets -> bucket 100, 50 buckets -> bucket 25)
            """
            return int(round(self.budget.priority, 2) * 100) * Config.BAG_NUMBER_OF_BUCKETS / 100

        def decay(self, multiplier=Config.PRIORITY_DECAY_MULTIPLIER):
            """
                Decay this item's priority
            """
            new_priority = self.budget.priority * multiplier
            if new_priority < self.budget.quality: return # priority can't go below quality
            self.budget.priority = round(new_priority, 3)

        class Budget:
            """
                Budget deciding the proportion of the system's time-space resources to allocate to a Bag Item.
                Priority determines how likely an item is to be selected,
                Quality defines the Item's base priority (its lowest possible priority)
            """
            def __init__(self, priority=0.99, quality=0.01):
                self.priority = priority
                self.quality = quality

class Bag(ItemContainer):
    """
        Probabilistic priority-queue

        --------------------------------------------

        An array of buckets, where each bucket holds items of a certain priority
        (e.g. 100 buckets, bucket 1 - hold items with 0.01 priority,  bucket 50 - hold items with 0.50 priority)
    """

    def __init__(self, item_type, capacity=Config.BAG_DEFAULT_CAPACITY):
        self.number_of_buckets = Config.BAG_NUMBER_OF_BUCKETS  # number of buckets in the bag (the bag's granularity)
        self.buckets = dict()  # for accessing items by priority
        self.current_bucket_number = 0  # keeps track of the Bag's current bucket number
        self.count = 0

        # initialize buckets
        for i in range(0, self.number_of_buckets):
            self.buckets[i] = []

        ItemContainer.__init__(self, item_type=item_type,capacity=capacity)

    def __len__(self):
        return self.count

    def __iter__(self):
        return iter(list(self.item_lookup_dict.values()).__reversed__())

    def put(self, item):
        """
            Place an Item into the bag.
            If it's new, wraps it in the Item object and places it into the lookup table

            :param Bag Item to place into the Bag

            :returns Item purged from the Bag if the inserted item causes an overflow
        """
        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)

        ItemContainer._put_into_lookup_dict(self, item)  # Item Container
        # put item into bucket
        self.buckets[item.get_target_bucket_number()].append(item)
        item.current_bucket_number = item.get_target_bucket_number()

        # increase Bag count
        self.count += 1

        # remove lowest priority item if over capacity
        purged_item = None
        if len(self) > self.capacity:
            purged_item = self._take_min()
        return purged_item

    def peek(self, key=None):
        """
            Peek an object from the bag using its key.
            If key is None, peeks probabilistically

            :returns An item peeked from the Bag; None if item could not be taken from the Bag
        """
        if self.count == 0: return None  # no items

        if key is None:
            item, _ = self._peek_probabilistically()
        else:
            item = ItemContainer.peek_using_key(self,key=key)

        return item

    def peek_max(self):
        """
            Peek an object in the highest priority bucket

            Returns None if Bag is empty
        """
        if self.count == 0: return None
        self._move_to_max_nonempty_bucket()
        item, _ = self._peek_random_item_from_current_bucket()
        return item


    def take_using_key(self, key):
        """
        Take an item from the bag using the key

        :param key: key of the item to remove from the Bag
        :return: the item which was removed from the bucket
        """
        assert (key in self.item_lookup_dict), "Given key does not exist in this bag"

        item = ItemContainer.peek_using_key(self, key=key)
        self.buckets[item.current_bucket_number].remove(item)  # remove item reference from bucket
        self.count = self.count - 1  # decrement bag count

        ItemContainer._take_from_lookup_dict(self, key)

        return item

    def _take_min(self):
        """
            Selects the lowest priority bucket, and removes an item from it.
            Also removes the item from the Item Lookup Dict

            :returns the lowest priority item taken from the Bag
        """
        # store old index so we can restore it
        oldidx = self.current_bucket_number

        self._move_to_min_nonempty_bucket()

        # peek a random item from the bucket
        _, randidx = self._peek_random_item_from_current_bucket()

        # remove the item from the bucket
        item = self.buckets[self.current_bucket_number].pop(randidx)

        self.count = self.count - 1  # decrement bag count

        # remove item reference from lookup table
        ItemContainer._take_from_lookup_dict(self, key=item.key)

        # restore original index
        self.current_bucket_number = oldidx

        return item

    def _peek_probabilistically(self):
        """
            Probabilistically selects a priority value / bucket, then peeks an item from that bucket.

            :returns (item, index of item in the current bucket)
        """
        if self.count == 0: return None, None
        # probabilistically select a priority bucket
        self._move_to_next_nonempty_bucket()  # try next non-empty bucket
        rnd = random.random()  # randomly generated number in [0.0, 1.0)
        bucket_probability = self.current_bucket_number / self.number_of_buckets

        while rnd >= bucket_probability:
            # bucket was not selected, try next bucket
            self._move_to_next_nonempty_bucket()  # try next non-empty bucket
            rnd = random.random()  # randomly generated number in [0.0, 1.0)
            bucket_probability = self.current_bucket_number / self.number_of_buckets

        # peek a random item from the bucket
        item, randidx = self._peek_random_item_from_current_bucket()

        return item, randidx

    def _peek_random_item_from_current_bucket(self):
        """
            Picks an item from the current bucket using uniform randomness.

            :returns (item, index of item in current bucket)
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
        assert self.count > 0, "Cannot select non-empty bucket in empty Bag"
        self._move_upward_to_next_bucket()
        while len(self.buckets[self.current_bucket_number]) == 0:
            self._move_upward_to_next_bucket()

    def _move_to_max_nonempty_bucket(self):
        """
            Select the highest value non-empty bucket

        """
        assert self.count > 0,"Cannot select non-empty bucket in empty Bag"
        self.current_bucket_number = self.number_of_buckets - 1
        self._move_downward_to_next_bucket()
        while len(self.buckets[self.current_bucket_number]) == 0:
            self._move_downward_to_next_bucket()

    def _move_to_min_nonempty_bucket(self):
        """
            Select the highest value non-empty bucket

        """
        assert self.count > 0,"Cannot select non-empty bucket in empty Bag"
        # move to lowest non-empty priority bucket
        self.current_bucket_number = 0
        self._move_to_next_nonempty_bucket()

    def _move_downward_to_next_bucket(self):
        """
            Select the next bucket below the currently selected bucket
        """
        self.current_bucket_number = (self.current_bucket_number - 1) % self.number_of_buckets

    def _move_upward_to_next_bucket(self):
        """
            Select the next bucket above the currently selected bucket
        """
        self.current_bucket_number = (self.current_bucket_number + 1) % self.number_of_buckets

class Depq():
    def __init__(self):
        self.depq = depq.DEPQ(iterable=None, maxlen=None)  # maxheap depq

    def __iter__(self):
        return iter(self.depq)

    def __len__(self):
        return len(self.depq)

    def _insert_object(self, object, priority):
        self.depq.insert(object, priority)

    def _extract_max(self):
        """
            Extract Item with highest priority from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        max = self.depq.popfirst()[0]
        return max

    def _extract_min(self):
        """
            Extract Item with lowest priority from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        min = self.depq.poplast()[0]
        return min

    def peek_max(self):
        """
            Peek Item with highest priority from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        i = self.depq.first()
        return i

    def peek_min(self):
        """
            Peek Item with lowest priority from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        return self.depq.last()

class Buffer(ItemContainer, Depq):
    """
        Priority-Queue
    """
    def __init__(self, item_type, capacity=Config.BUFFER_DEFAULT_CAPACITY):
        self.capacity=capacity
        ItemContainer.__init__(self, item_type=item_type,capacity=capacity) # Item Container
        Depq.__init__(self) #Depq


    def put(self, item):
        """
            Insert an Item into the Buffer, sorted by priority.

            :returns Item that was purged if the inserted item caused an overflow
        """
        if not isinstance(item,ItemContainer.Item):
            item = ItemContainer.Item(item, self.get_next_item_id())

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
    def __init__(self,item_type,capacity=Config.BUFFER_DEFAULT_CAPACITY):
        ItemContainer.__init__(self,item_type=item_type,capacity=capacity)
        self.fifo = queue.Queue()

    def __len__(self):
        return self.fifo.qsize()

    def put(self, item):
        """
            Insert an Item into the Buffer, sorted by priority.

            :returns Item that was purged if the inserted item caused an overflow
        """
        if not isinstance(item,ItemContainer.Item):
            item = ItemContainer.Item(item, self.get_next_item_id())

        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)

        self.fifo.put(item)
        ItemContainer._put_into_lookup_dict(self, item)  # Item Container

        purged_item = None
        if len(self) > self.capacity:
            purged_item = self.fifo.get()
            self._take_from_lookup_dict(purged_item.key)

        return purged_item

    def take(self):
        """
            Take the max item from the Buffer
            :return:
        """
        if len(self) == 0: return None
        item = self.fifo.get()
        self._take_from_lookup_dict(item.key)

        return item


class Table(Depq):
    """
        NARS Table, stored within Concepts.
        Tables store Narsese sentences using a double ended priority queue, sorted by confidence
        It purges lowest-confidence items when it overflows.
    """

    def __init__(self, item_type=NALGrammar.Judgment, capacity=Config.TABLE_DEFAULT_CAPACITY):
        self.item_type = item_type
        self.capacity = capacity
        Depq.__init__(self)

    def put(self, sentence: NALGrammar.Sentence):
        """
            Insert a Sentence into the depq, sorted by confidence.
        """
        assert (isinstance(sentence,self.item_type)), "Cannot insert sentence into a Table of different punctuation"
        Depq._insert_object(self, sentence, sentence.value.confidence)

        if len(self) > self.capacity:
            Depq._extract_min(self)

    def peek(self):
        """
            Peek item with highest priority from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self) == 0: return None
        return Depq.peek_max(self)


class Task:
    """
       NARS Task
    """

    def __init__(self, sentence, is_input_task=False):
        NALGrammar.assert_sentence(sentence)
        self.sentence = sentence
        self.creation_timestamp: int = Global.Global.get_current_cycle_number()  # save the task's creation time
        self.is_from_input: bool = is_input_task
        self.needs_initial_processing: bool = True
        #only used for question tasks
        self.needs_to_be_answered_in_output: bool = is_input_task

    def __str__(self):
        return self.sentence.get_formatted_string_no_id()



# Asserts
def assert_task(j):
    assert (isinstance(j, Task)), str(j) + " must be a Task"
