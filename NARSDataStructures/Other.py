import random

import Asserts
import NALGrammar.Sentences
import Config
import Global
import depq

"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""

class Depq():
    def __init__(self):
        self.depq = depq.DEPQ(iterable=None, maxlen=None)  # maxheap depq

    def __iter__(self):
        return iter(self.depq)

    def __len__(self):
        return len(self.depq)

    def __getitem__(self, i):
        return self.depq[i][0]

    def insert_object(self, object, priority):
        self.depq.insert(object, priority)

    def extract_max(self):
        """
            Extract Item with highest priority from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self.depq) == 0: return None
        max = self.depq.popfirst()[0]
        return max

    def extract_min(self):
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

class Table(Depq):
    """
        NARS Table, stored within Concepts.
        Tables store Narsese sentences using a double ended priority queue, where priority = sentence confidence
        Sorted by highest-confidence.
        It purges lowest-confidence items when it overflows.
    """

    def __init__(self, item_type, capacity=Config.TABLE_DEFAULT_CAPACITY):
        self.item_type = item_type
        self.capacity = capacity
        Depq.__init__(self)

    def put(self, sentence):
        """
            Insert a Sentence into the depq, sorted by confidence (time-projected confidence if it's an event).
        """
        assert (isinstance(sentence,self.item_type)), "Cannot insert sentence into a Table of different punctuation"

        confidence = sentence.value.confidence
        if sentence.is_event():
            confidence = sentence.get_present_value().confidence

        Depq.insert_object(self, sentence, confidence)

        if len(self) > self.capacity:
            Depq.extract_min(self)

    def take(self):
        """
            Take item with highest confidence from the depq
            O(1)
        """
        return Depq.extract_max(self)

    def peek(self):
        """
            Peek item with highest confidence from the depq
            O(1)

            Returns None if depq is empty
        """
        return Depq.peek_max(self)

    def peek_random(self):
        """
            Peek random item from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self) == 0: return None
        return self[round(random.random() * (len(self)-1))]

    def peek_highest_confidence_interactable(self, j):
        """
            Returns the best sentence in this table that j may interact with
            None if there are none.
            O(N)

        :param j:
        :return:
        """
        for (belief, confidence) in self: # loop starting with max confidence
            if NALGrammar.Sentences.may_interact(j,belief):
                return belief
        return None


class Task:
    """
       NARS Task
    """

    def __init__(self, sentence, is_input_task=False):
        Asserts.assert_sentence(sentence)
        self.sentence = sentence
        self.creation_timestamp: int = Global.Global.get_current_cycle_number()  # save the task's creation time
        self.is_from_input: bool = is_input_task
        #only used for question tasks
        self.needs_to_be_answered_in_output: bool = is_input_task

    def get_term(self):
        return self.sentence.statement

    def __str__(self):
        return "TASK: " + self.sentence.get_formatted_string_no_id()
