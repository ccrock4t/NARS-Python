"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import random

from NARSDataStructures.ItemContainers import ItemContainer
import Config

class Bag(ItemContainer):
    """
        Probabilistic priority-queue

        --------------------------------------------

        An array of buckets, where each bucket holds items of a certain priority
        (e.g. 100 buckets, bucket 1 - hold items with 0.01 priority,  bucket 50 - hold items with 0.50 priority)
    """

    def __init__(self, item_type, capacity):
        self.number_of_buckets = Config.BAG_NUMBER_OF_BUCKETS  # number of buckets in the bag (the bag's granularity)
        self.buckets = dict()  # for accessing items by priority
        self.current_bucket_number = 0  # keeps track of the Bag's current bucket number
        self.count = 0

        # initialize buckets between 0 and number-of-buckets minus 1
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

            :param Bag Item to place into the Bag
            :returns Item purged from the Bag if the inserted item causes an overflow
        """
        assert (isinstance(item.object, self.item_type)), "item object must be of type " + str(self.item_type)

        # increase Bag count
        self.count += 1

        ItemContainer._put_into_lookup_dict(self, item)  # Item Container
        # put item into bucket
        self.buckets[item.get_target_bucket_number()].append(item)
        item.current_bucket_number = item.get_target_bucket_number()

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
        self._move_up_to_max_nonempty_bucket()
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

    def _move_up_to_max_nonempty_bucket(self):
        """
            Select the highest value non-empty bucket

        """
        assert self.count > 0,"Cannot select non-empty bucket in empty Bag"
        self.current_bucket_number = self.number_of_buckets - 1 # first check highest bucket
        while len(self.buckets[self.current_bucket_number]) == 0:
            self._move_down_to_next_bucket()

    def _move_to_min_nonempty_bucket(self):
        """
            Select the highest value non-empty bucket

        """
        assert self.count > 0,"Cannot select non-empty bucket in empty Bag"
        # move to lowest non-empty priority bucket
        self.current_bucket_number = 0
        self._move_to_next_nonempty_bucket()

    def _move_down_to_next_bucket(self):
        """
            Select the next bucket below the currently selected bucket
        """
        self.current_bucket_number = (self.current_bucket_number - 1) % self.number_of_buckets

    def _move_upward_to_next_bucket(self):
        """
            Select the next bucket above the currently selected bucket
        """
        self.current_bucket_number = (self.current_bucket_number + 1) % self.number_of_buckets