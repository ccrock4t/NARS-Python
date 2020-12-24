import Config
import random

class Bag:
    """
        Probabilistic priority-queue

        Probabilistically selects a random priority value / bucket, then chooses the item in that bucket.
        (If multiple items have the same priority level, one is randomly selected)
    """
    def __init__(self, item_type):
        self.item_type = item_type

        self.capacity = Config.default_bag_capacity
        self.number_of_buckets = Config.default_bag_number_of_buckets

        self.item_lookup_table = dict() # for accessing item by key
        self.priority_buckets = dict() # for accessing items by priority
        self.current_bucket_number = 0 # keeps track of current bucket number

        for i in range(0, self.number_of_buckets):
            self.priority_buckets[i] = []


    def put(self, object):
        """
            Convert an object into an item and place the item in the bag
        """
        assert (isinstance(object, self.item_type)), "item must be of type " + str(self.item_type)
        if str(object) not in self.item_lookup_table:
            item = Bag.Item(object)
            self.item_lookup_table[str(object)] = item

    def get(self, key):
        """
            Get an item from the bag, either probabilistically or from its key
        """
        if key is None:
            return self.probabilistically_select_item()
        return self.item_lookup_table[key]

    def probabilistically_select_item(self):
        """
            Get an item from the bag probabilistically
        """
        rnd = random.random()  # randomly generated number in [0.0, 1.0)
        self.move_to_next_nonempty_bucket()  # try next non-empty bucket
        # select the current bucket only if rnd is smaller than
        # the ratio of the bucket number to total number of buckets
        # (e.g. the first bucket will never be selected (0% priority),
        # the last bucket is guaranteed to be selected (100% priority))
        while rnd >= (self.current_bucket_number / (self.number_of_buckets - 1)):
            rnd = random.random()  # randomly generated number in [0.0, 1.0)
            self.move_to_next_nonempty_bucket() # try next non-empty bucket

        # select item from selected bucket
        item = self.get_item_from_current_bucket()
        return item

    def get_item_from_lookup_table(self, key):
        #todo actually remove the item from the bucket
        item = self.item_lookup_table[key]
        return self.priority_buckets[self.current_bucket_number].pop()

    def get_item_from_current_bucket(self):
        """
            Get an item from the currently selected bucket
        """
        return self.priority_buckets[self.current_bucket_number].pop()

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
            self.budget = Bag.Item.Budget(priority=0.9, )

        class Budget:
            def __init__(self, priority=0, durability=0, quality=0):
                self.priority = priority
                self.durability = durability
                self.quality = quality

class Buffer:
    """
        Time-restricted Bag
    """
    def __init__(self):
        self.capacity = Config.default_bag_capacity
