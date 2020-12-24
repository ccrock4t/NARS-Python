import Config
import random
import NALInferenceRules

class Bag:
    """
        Probabilistic priority-queue

        --------------------------------------------

        An array of buckets, where each bucket holds items of a certain priority
        (e.g. 100 buckets, bucket 1 - hold items with 0.01 priority,  bucket 50 - hold items with 0.50 priority)
    """
    def __init__(self, item_type):
        self.item_type = item_type

        self.capacity = Config.DEFAULT_BAG_CAPACITY
        self.number_of_buckets = Config.DEFAULT_BAG_NUMBER_OF_BUCKETS
        self.item_lookup_table = dict() # for accessing item by key
        self.priority_buckets = dict() # for accessing items by priority

        self.current_bucket_number = 0 # keeps track of the Bag's current bucket number
        self.count = 0

        for i in range(0, self.number_of_buckets):
            self.priority_buckets[i] = []

    def put_new_item(self, object):
        """
            Convert an object into an item and place the item in the bag
        """
        assert (isinstance(object, self.item_type)), "item must be of type " + str(self.item_type)
        if str(object) not in self.item_lookup_table:
            # create item
            item = Bag.Item(object)
            key = item.key

            #put into lookup table and bucket
            self.item_lookup_table[key] = item
            self.priority_buckets[item.get_new_bucket_number()].append(item)

            self.count = self.count + 1


    def put(self, item):
        """
            Place an item in the bag
        """
        assert (isinstance(item, Bag.Item)), "item must be of type " + str(Bag.Item)
        if item.key not in self.item_lookup_table:
            #put into lookup table and bucket
            self.item_lookup_table[item.key] = item
            self.priority_buckets[item.get_new_bucket_number()].append(item)

            self.count = self.count + 1

    def get(self, object=None):
        """
            Get an item from the bag, either probabilistically or from its object key

            Input:
                object - if object is not passed, probabilistically removes it's corresponding item from the bag
                        if object is passed, the item is not removed from the bag
        """
        if self.count == 0:
            return None

        self.count = self.count - 1

        if object is None:
            return self.remove_item_probabilistically()
        return self.remove_item_by_key(str(object))

    def remove_item_by_key(self, key):
        assert(key in self.item_lookup_table),"Given key does not exist in this bag"
        item = self.item_lookup_table.pop(key)
        self.priority_buckets[item.current_bucket_number].remove(item)
        return item

    def remove_item_probabilistically(self):
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

        # select item from selected bucket
        item = self.remove_random_item_from_current_bucket()

        #also remove from lookup table
        self.item_lookup_table.pop(item.key)

        return item

    def remove_random_item_from_current_bucket(self):
        """
            Get an item from the currently selected bucket
        """
        rnd = random.random()  # randomly generated number in [0.0, 1.0)
        maxidx = len(self.priority_buckets[self.current_bucket_number]) - 1
        randidx = int(round(rnd * maxidx))
        return self.priority_buckets[self.current_bucket_number].pop(randidx)

    def move_to_next_nonempty_bucket(self):
        """
            Select the next non-empty bucket after the currently selected bucket
        """
        self.move_to_next_bucket()
        while len(self.priority_buckets[self.current_bucket_number]) == 0:
            self.move_to_next_bucket()

    def move_to_next_bucket(self):
        """
            Select the next bucket after the currently selected bucket
        """
        self.current_bucket_number = (self.current_bucket_number + 1) % self.number_of_buckets

    class Item:
        """
            Item in a bag

            Consists of:
                object (e.g. Concept, Task, etc.)

                budget ($priority;durability;quality$)
        """
        def __init__(self, object):
            self.object = object
            self.budget = Bag.Item.Budget(priority=0.9, durability=0.9, quality=0.9)
            self.key = str(object)
            self.current_bucket_number = self.get_new_bucket_number()

        def get_new_bucket_number(self):
            """
                Output: The bucket number this item belongs in
                This item's priority rounded to 2 decimals * 100 (as an int)
            """
            return int(round(self.budget.priority, 2) * 100)

        class Budget:
            def __init__(self, priority=0, durability=0, quality=0):
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
    """
    def __init__(self):
        self.capacity = Config.DEFAULT_BAG_CAPACITY
