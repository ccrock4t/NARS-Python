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
import NARSDataStructures.Other
import NARSDataStructures.Bag
import NALInferenceRules


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
        #self.item_archive = {}

    def __contains__(self, object):
        """
            Purpose:
                Check if the object is contained in the Bag by checking whether its key is in the item lookup table

        :param object: object to look for in the Bag
        :return: True if the item is in the Bag;
                    False otherwise
        """
        key = Item.get_key_from_object(object)
        return self.item_lookup_dict.get(key, None) is not None

    def __iter__(self):
        return iter(self.item_lookup_dict.values())

    def __getitem__(self, key):
        return self.item_lookup_dict[key]

    def _clear(self):
        self.item_lookup_dict = dict()
        self.next_item_id = 0

    def PUT_NEW(self, object):
        """
            Place a NEW Item into the container.
        """
        item = NARSDataStructures.ItemContainers.Item(object, self.get_next_item_id())
        self._put_into_lookup_dict(item)  # Item Container
        return item

    def _put_into_lookup_dict(self, item):
        """
            Puts item into lookup table and GUI
            :param item: put an Item into the lookup dictionary.
        """
        # put item into lookup table
        self.item_lookup_dict[item.key] = item

        if Config.GUI_USE_INTERFACE:
            Global.Global.print_to_output(str(item), data_structure=self)  # draw to GUI
            #self.item_archive[item.key] = item

    def _take_from_lookup_dict(self, key):
        """
            Removes an Item from the lookup dictionary using its key,
            and returns the Item.

        :param key: Key of the Item to remove.
        :return: The Item that was removed.
        """
        item = self.item_lookup_dict.pop(key)  # remove item reference from lookup table

        if Config.GUI_USE_INTERFACE:
            Global.Global.remove_from_output(str(item), data_structure=self)

        return item


    def _take_min(self):
        assert False, "Take smallest priority item not defined for generic Item Container!"

    def get_next_item_id(self) -> int:
        self.next_item_id += 1
        return self.next_item_id - 1

    def peek_from_item_archive(self, key):
        return self.item_archive.get(key, None)

    def peek_using_key(self, key=None):
        """
            Peek an Item using its key

            :param key: Key of the item to peek
            :return: Item peeked from the data structure
        """
        assert key is not None, "Key cannot be none when peeking with a key!"
        return self.item_lookup_dict.get(key, None)


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
        self.bucket = None
        self.object = object
        self.id = id
        priority = None

        quality = None
        if isinstance(object, NARSDataStructures.Other.Task):
            if isinstance(object.sentence, NALGrammar.Sentences.Judgment):
                priority = object.sentence.get_present_value().confidence


        elif isinstance(object, NARSMemory.Concept):
            if isinstance(object.term, NALGrammar.Terms.SpatialTerm):
                pass
            elif isinstance(object.term, NALGrammar.Terms.StatementTerm) and not object.term.is_first_order():
                pass
            # if isinstance(object.term,NALGrammar.Terms.CompoundTerm) and object.term.connector == NALSyntax.TermConnector.Negation:
            #     priority = 0.0
            #     quality = 0.0
            # if isinstance(object.term,NALGrammar.Terms.StatementTerm) and object.term.is_first_order():
            #      priority = 0.0
            #      quality = 0.8

        # assign ID
        if isinstance(object, NARSDataStructures.Other.Task):
            self.key = id
        else:
            self.key = Item.get_key_from_object(object)


        self.budget = Item.Budget(priority=priority, quality=quality)

    @classmethod
    def get_key_from_object(cls, object):
        """
            Returns a key that uniquely identifies the given object.

            This is essentially a universal hash function for NARS objects

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
        return NALSyntax.StatementSyntax.BudgetMarker.value \
                + "{:.5f}".format(self.budget.get_priority()) \
               + NALSyntax.StatementSyntax.TruthValDivider.value \
               + "{:.5f}".format(self.budget.get_quality()) \
               + NALSyntax.StatementSyntax.BudgetMarker.value \
               + " " \
                + Global.Global.MARKER_ITEM_ID \
                + str(self.id) + Global.Global.MARKER_ID_END \
                + str(self.object)



    def get_gui_info(self):
        dict = {}
        dict[NARSGUI.NARSGUI.KEY_KEY] = self.key
        dict[NARSGUI.NARSGUI.KEY_CLASS_NAME] = type(self.object).__name__
        dict[NARSGUI.NARSGUI.KEY_OBJECT_STRING] = str(self.object)
        dict[NARSGUI.NARSGUI.KEY_TERM_TYPE] = type(self.object.get_term()).__name__
        if isinstance(self.object, NARSMemory.Concept):
            dict[NARSGUI.NARSGUI.KEY_IS_POSITIVE] = "True" if self.object.is_positive() else "False"
            if len(self.object.desire_table) > 0:
                dict[NARSGUI.NARSGUI.KEY_PASSES_DECISION] = "True" if NALInferenceRules.Local.Decision(
                    self.object.desire_table.peek()) else "False"
            else:
                dict[NARSGUI.NARSGUI.KEY_PASSES_DECISION] = None
            dict[NARSGUI.NARSGUI.KEY_EXPECTATION] = self.object.get_expectation()
            dict[NARSGUI.NARSGUI.KEY_LIST_BELIEFS] = [str(belief[0]) for belief in self.object.belief_table]
            dict[NARSGUI.NARSGUI.KEY_LIST_DESIRES] = [str(desire[0]) for desire in self.object.desire_table]
            dict[NARSGUI.NARSGUI.KEY_LIST_TERM_LINKS] = [str(termlink.object) for termlink in self.object.term_links]
            dict[NARSGUI.NARSGUI.KEY_LIST_PREDICTION_LINKS] = [str(predictionlink.object) for predictionlink in
                                                               self.object.prediction_links]
            dict[NARSGUI.NARSGUI.KEY_LIST_EXPLANATION_LINKS] = [str(explanationlink.object) for explanationlink in
                                                                self.object.explanation_links]
            dict[NARSGUI.NARSGUI.KEY_CAPACITY_BELIEFS] = str(self.object.belief_table.capacity)
            dict[NARSGUI.NARSGUI.KEY_CAPACITY_DESIRES] = str(self.object.desire_table.capacity)
            dict[NARSGUI.NARSGUI.KEY_CAPACITY_TERM_LINKS] = str(self.object.term_links.capacity)
            dict[NARSGUI.NARSGUI.KEY_CAPACITY_PREDICTION_LINKS] = str(self.object.prediction_links.capacity)
            dict[NARSGUI.NARSGUI.KEY_CAPACITY_EXPLANATION_LINKS] = str(self.object.explanation_links.capacity)
        elif isinstance(self.object, NARSDataStructures.Other.Task):
            dict[NARSGUI.NARSGUI.KEY_SENTENCE_STRING] = str(self.object.sentence)
            dict[NARSGUI.NARSGUI.KEY_LIST_EVIDENTIAL_BASE] = [str(evidence) for evidence in
                                                              self.object.sentence.stamp.evidential_base]
            dict[NARSGUI.NARSGUI.KEY_LIST_INTERACTED_SENTENCES] = []

        return dict

    class Budget:
        """
            Budget deciding the proportion of the system's time-space resources to allocate to a Bag Item.
            Priority determines how likely an item is to be selected,
            Quality defines the Item's base priority (its lowest possible priority)
        """

        def __init__(self, priority=None, quality=None):
            if quality is None: quality = 0
            self.set_quality(quality)

            if priority is None: priority = quality
            self.set_priority(priority)

        def __str__(self):
            return NALSyntax.StatementSyntax.BudgetMarker.value \
                   + str(self.get_priority()) \
                   + NALSyntax.StatementSyntax.TruthValDivider.value \
                   + str(self.get_quality()) \
                   + NALSyntax.StatementSyntax.BudgetMarker.value

        def set_priority(self, value):
            # if value < self.get_quality(): value = self.get_quality()  # priority can't go below quality
            if value > 0.99999999: value = 0.99999999  # priority can't got too close to 1
            if value < 0: value = 0  # priority can't go below 0
            self._priority = value

        def set_quality(self, value):
            if value > 0.99999999: value = 0.99999999  # quality can't got too close to 1
            if value < 0: value = 0  # priority can't go below 0
            self._quality = value

        def get_priority(self):
            return self._priority

        def get_quality(self):
            return self._quality
