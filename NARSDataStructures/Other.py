import random
import timeit as time
from typing import List

import Asserts
import NALGrammar.Sentences
import Config
import Global
import depq
import NALInferenceRules

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

    def remove(self, item):
        return self.depq.remove(item)

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

    def clear(self):
        while len(self) > 0:
            self.take()

    def put(self, sentence):
        """
            Insert a Sentence into the depq, sorted by confidence (time-projected confidence if it's an event).
        """
        assert (isinstance(sentence, self.item_type)), "Cannot insert sentence into a Table of different punctuation"

        if len(self) > 0:
            if sentence.is_event():
                current_event = self.take()
                sentence = NALInferenceRules.Local.Revision(sentence, current_event)
            else:
                existing_interactable = self.peek_highest_confidence_interactable(sentence)
                if existing_interactable is not None:
                    revised = NALInferenceRules.Local.Revision(sentence, existing_interactable)
                    priority = revised.get_present_value().confidence
                    Depq.insert_object(self, revised, priority)


        priority = sentence.get_present_value().confidence
        Depq.insert_object(self, sentence, priority)

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
        max = self.take()
        if max is not None:
            self.put(max)
        return max

    def peek_random(self):
        """
            Peek random item from the depq
            O(1)

            Returns None if depq is empty
        """
        if len(self) == 0: return None
        return random.choice(self)

    def peek_highest_confidence_interactable(self, j):
        """
            Returns the best sentence in this table that j may interact with
            None if there are none.
            O(N)

        :param j:
        :return:
        """
        for (belief, confidence) in self:  # loop starting with max confidence
            if NALGrammar.Sentences.may_interact(j, belief):
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
        # only used for question tasks
        self.needs_to_be_answered_in_output: bool = is_input_task

    def get_term(self):
        return self.sentence.statement

    def __str__(self):
        return "TASK: " + self.sentence.get_term_string_no_id()

class QuadTree:


    def __init__(self, ROOTLEAFID=None):
        self.children: List[QuadTree] = []
        self.values: List[NALGrammar.Sentences.Judgment] = []
        self.id = None
        self.LEAFID = ROOTLEAFID if ROOTLEAFID is not None else [0]
        self.MAXLEAFID = 32 # todo - make this vary


    def Create4ChildrenRecursive(self, depth):
        if(depth == 0):
            self.id = (self.LEAFID[0] // self.MAXLEAFID, self.LEAFID[0] % self.MAXLEAFID) #(y,x)
            self.LEAFID[0] += 1
            return

        for _ in range(4):
            child = QuadTree(ROOTLEAFID=self.LEAFID)
            child.Create4ChildrenRecursive(depth-1)
            self.children.append(child)
