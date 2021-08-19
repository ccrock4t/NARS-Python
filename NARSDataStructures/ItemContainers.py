"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import Global
import NALSyntax
import NARSGUI
import NALGrammar
import NARSMemory
import Config
from NARSDataStructures.Other import Task
import NALInferenceRules


class ItemContainer:
    """
        Base Class for data structures which contain "Items", as defined in this class.

        Examples of Item Containers include Bag and Buffer.
    """
    item_archive = {}

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
        return Item.get_key_from_object(object) in self.item_lookup_dict

    def __iter__(self):
        return iter(self.item_lookup_dict.values())

    def _put_into_lookup_dict(self, item):
        """
            Puts item into lookup table and GUI
            :param item: put an Item into the lookup dictionary.
        """
        # put item into lookup table
        self.item_lookup_dict[item.key] = item

        if Config.gui_use_interface:
            Global.Global.print_to_output(str(item), data_structure=self)
            ItemContainer.item_archive[item.key] = item

    def _take_from_lookup_dict(self, key):
        """
            Removes an Item from the lookup dictionary using its key,
            and returns the Item.

        :param key: Key of the Item to remove.
        :return: The Item that was removed.
        """
        item = self.item_lookup_dict.pop(key)  # remove item reference from lookup table

        if Config.gui_use_interface:
            Global.Global.remove_from_output(str(item), data_structure=self)

        return item

    def put_new(self, object):
        item = Item(object, self.get_next_item_id())
        return self.put(item)

    def _take_min(self):
        assert False,"Take smallest priority item not defined for generic Item Container!"

    def get_next_item_id(self) -> int:
        self.next_item_id += 1
        return self.next_item_id - 1

    @classmethod
    def peek_from_item_archive(cls,key):
        if key not in ItemContainer.item_archive: return None
        return ItemContainer.item_archive[key]

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
            if isinstance(object.sentence, NALGrammar.Sentences.Judgment):
                priority = object.sentence.value.confidence
            else:
                priority = 0.95
            quality = 0.010
        elif isinstance(object, NARSMemory.Concept):
            quality = 0.95
            priority = 0.990 / object.term.syntactic_complexity
        elif isinstance(object, NALGrammar.Sentences.Sentence):
            priority = object.value.confidence
            quality = 0.500

        if priority is not None:
            if isinstance(object, Task):
                self.key = id
            else:
                self.key = Item.get_key_from_object(object)
            self.budget = Item.Budget(priority=priority, quality=quality)
        else:
            self.key = str(object)
            self.budget = Item.Budget()

        self.current_bucket_number = self.get_target_bucket_number()

    @classmethod
    def get_key_from_object(cls, object):
        """
            :param object:
            :return: key for object
        """
        key = None
        if isinstance(object, NARSMemory.Concept):
            key = str(object.term)
        elif isinstance(object, NALGrammar.Sentences.Sentence):
            key = str(object.stamp.id)
        else:
            key = str(object)
        return key

    def __str__(self):
        return Global.Global.MARKER_ITEM_ID \
               + str(self.id) + Global.Global.MARKER_ID_END \
               + str(self.object) \
               + " " \
               + NALSyntax.StatementSyntax.BudgetMarker.value \
               + "{:.3f}".format(self.budget.priority) \
               + NALSyntax.StatementSyntax.BudgetMarker.value


    def get_target_bucket_number(self):
        """
            Returns: The Bag bucket number this item belongs in according to its priority.

            It is calculated as this item's priority [0,1] converted to a corresponding probability
            based on Bag granularity
            (e.g. Priority=0.5, 100 buckets -> bucket 50, 200 buckets -> bucket 100, 50 buckets -> bucket 25)
        """
        return min(int(round(self.budget.priority, 2) * 100) * Config.BAG_NUMBER_OF_BUCKETS / 100, Config.BAG_NUMBER_OF_BUCKETS - 1)

    def strengthen(self,multiplier= Config.PRIORITY_STRENGTHEN_VALUE):
        """
            Increase this item's priority to a high value
        """
        self.budget.priority = NALInferenceRules.ExtendedBooleanOperators.bor(self.budget.priority,)
        if self.budget.priority > 0.95: self.budget.priority = 0.95

    def decay(self, multiplier=Config.PRIORITY_DECAY_MULTIPLIER):
        """
            Decay this item's priority
        """
        new_priority = self.budget.priority * multiplier
        if new_priority < self.budget.quality: return # priority can't go below quality
        self.budget.priority = round(new_priority, 3)

    def get_gui_info(self):
        dict = {}
        dict[NARSGUI.NARSGUI.KEY_KEY] = self.key
        dict[NARSGUI.NARSGUI.KEY_CLASS_NAME] = type(self.object).__name__
        dict[NARSGUI.NARSGUI.KEY_OBJECT_STRING] = str(self.object)
        dict[NARSGUI.NARSGUI.KEY_TERM_TYPE] = type(self.object.get_term()).__name__
        if isinstance(self.object, NARSMemory.Concept):
            dict[NARSGUI.NARSGUI.KEY_IS_POSITIVE] = "True" if self.object.is_positive() else "False"
            if len(self.object.desire_table) > 0:
                dict[NARSGUI.NARSGUI.KEY_PASSES_DECISION] = "True" if NALInferenceRules.Local.Decision(self.object.desire_table.peek()) else "False"
            else:
                dict[NARSGUI.NARSGUI.KEY_PASSES_DECISION] = None
            dict[NARSGUI.NARSGUI.KEY_EXPECTATION] = self.object.get_expectation()
            dict[NARSGUI.NARSGUI.KEY_LIST_BELIEFS] = [str(belief[0]) for belief in self.object.belief_table]
            dict[NARSGUI.NARSGUI.KEY_LIST_DESIRES] = [str(desire[0]) for desire in self.object.desire_table]
            dict[NARSGUI.NARSGUI.KEY_LIST_TERM_LINKS] = [str(termlink.object) for termlink in self.object.term_links]
            dict[NARSGUI.NARSGUI.KEY_LIST_PREDICTION_LINKS] = [str(predictionlink.object) for predictionlink in self.object.prediction_links]
            dict[NARSGUI.NARSGUI.KEY_LIST_EXPLANATION_LINKS] = [str(explanationlink.object) for explanationlink in self.object.explanation_links]
            dict[NARSGUI.NARSGUI.KEY_CAPACITY_BELIEFS] = str(self.object.belief_table.capacity)
            dict[NARSGUI.NARSGUI.KEY_CAPACITY_DESIRES] = str(self.object.desire_table.capacity)
            dict[NARSGUI.NARSGUI.KEY_CAPACITY_TERM_LINKS] = str(self.object.term_links.capacity)
            dict[NARSGUI.NARSGUI.KEY_CAPACITY_PREDICTION_LINKS] = str(self.object.prediction_links.capacity)
            dict[NARSGUI.NARSGUI.KEY_CAPACITY_EXPLANATION_LINKS] = str(self.object.explanation_links.capacity)
        elif isinstance(self.object, Task):
            dict[NARSGUI.NARSGUI.KEY_SENTENCE_STRING] = str(self.object.sentence)
            dict[NARSGUI.NARSGUI.KEY_LIST_EVIDENTIAL_BASE] = [str(evidence) for evidence in self.object.sentence.stamp.evidential_base]
            dict[NARSGUI.NARSGUI.KEY_LIST_INTERACTED_SENTENCES] = [str(interactedsentence) for interactedsentence in self.object.sentence.stamp.interacted_sentences]

        return dict

    class Budget:
        """
            Budget deciding the proportion of the system's time-space resources to allocate to a Bag Item.
            Priority determines how likely an item is to be selected,
            Quality defines the Item's base priority (its lowest possible priority)
        """
        def __init__(self, priority=0.99, quality=0.01):
            self.priority = priority
            self.quality = quality