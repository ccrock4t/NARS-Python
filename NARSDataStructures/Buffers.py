"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import math
import random
import timeit as time
from typing import Tuple, List

import Config
import Global
import NALSyntax
import NARSInferenceEngine
from NALGrammar.Sentences import Judgment
from NALGrammar.Values import TruthValue
from NALInferenceRules.TruthValueFunctions import F_Revision
from NARSDataStructures.Bag import Bag
from NARSDataStructures.ItemContainers import ItemContainer, Item
from NARSDataStructures.Other import Depq, Task, QuadTree
import NALInferenceRules
import NALGrammar
import numpy as np
import NARSDataStructures

class Buffer(ItemContainer, Depq):
    """
        Priority-Queue
    """

    def __init__(self, item_type, capacity):
        self.capacity = capacity
        ItemContainer.__init__(self, item_type=item_type, capacity=capacity)  # Item Container
        Depq.__init__(self)  # Depq

    def PUT_NEW(self, object):
        """
            Insert an Item into the Buffer, sorted by priority.

            :returns Item that was purged if the inserted item caused an overflow
        """
        assert (isinstance(object, self.item_type)), "item object must be of type " + str(self.item_type)
        item = NARSDataStructures.ItemContainers.Item(object, self.get_next_item_id())
        self._put_into_lookup_dict(item)  # Item Container

        Depq.insert_object(self, item, item.budget.get_priority())  # Depq

        purged_item = None
        if len(self) > self.capacity:
            purged_item = self.extract_min()
            self._take_from_lookup_dict(purged_item.key)

        return purged_item

    def take(self):
        """
            Take the max priority item
            :return:
        """
        if len(self) == 0: return None
        item = Depq.extract_max(self)
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


class SpatialBuffer():
    """
        Holds the current sensation signals in a spatial layout / array.

        The data is converted to Narsese when extracted.
    """
    MAX_PIXEL_VALUE = 255
    PREDICATE_NAME = 'Bright'

    def __init__(self, dimensions):
        """
        :param dimensions: dimensions of the 2d buffer as a tuple (y, x)
        """
        assert len(dimensions) == 2, "ERROR: Spatial buffer only support 2D structures"
        self.dimensions : Tuple = dimensions

        self.quadtree_leaves = np.empty(shape=(8,8), dtype=QuadTree)

        # total image
        # 1 node on level 0, the root
        self.quadtree : QuadTree = QuadTree()

        self.quadtree.Create4ChildrenRecursive(5) #2^5=32, therefore this allows for images that are 32x32 pixels, creating 1024 leaf nodes

        self.last_taken_img_array = None
        self.last_sentence = None
        self.quadtree_id = 0
        self.events: List[Judgment] = []

    def blank_image(self):
        self.set_image(np.empty(shape=self.dimensions))

    def set_image(self, img):
        self.img = img
        self.quadtree_id = 0
        self.events = []
        self.CalculateQuadTreeRecursive(self.quadtree)


    def CalculateQuadTreeRecursive(self, quad_tree: QuadTree):
        if len(quad_tree.children) == 0:
            # leaf node, so add the event
            y,x = quad_tree.id
            if y >= 28 or x >= 28: # MNIST images are 28x28
                pixel_value = float(0)
            else:
                pixel_value = float(self.img[y, x])
            f = pixel_value / SpatialBuffer.MAX_PIXEL_VALUE
            c = NALInferenceRules.HelperFunctions.get_unit_evidence()
            event = self.create_pixel_event(subject_name=str(y) + "_" + str(x), f=f, c=c)
            quad_tree.value = event
        else:
            for i in range(len(quad_tree.children)):
                child_node = quad_tree.children[i]
                self.CalculateQuadTreeRecursive(child_node)

            quad_tree.value = self.create_spatial_conjunction(quad_tree)

        Global.Global.NARS.process_judgment_sentence_initial(quad_tree.value)
        self.events.append(quad_tree.value)


    def create_pixel_event(self, subject_name: str, f: float, c: float):

        statement = NALGrammar.Terms.from_string("(" + subject_name + "-->" + SpatialBuffer.PREDICATE_NAME + ")")
        return NALGrammar.Sentences.Judgment(statement=statement,
                                      value=TruthValue(f, c),
                                      occurrence_time=None)

    def create_spatial_conjunction(self, quad_tree: QuadTree):
        """
        :param subset: 2d Array of positive (non-negated) sentences / events
        :return:
        """

        conjunction_truth_value = None
        for quad_child in quad_tree.children:
            sentence = quad_child.value
            truth_value: TruthValue = sentence.value
            if conjunction_truth_value is None:
                conjunction_truth_value = truth_value.Clone()
            else:
                conjunction_truth_value = F_Revision(conjunction_truth_value.frequency,
                                                     conjunction_truth_value.confidence,
                                                     truth_value.frequency,
                                                     truth_value.confidence)


            
        spatial_conjunction = self.create_pixel_event("QUAD" + str(self.quadtree_id),
                                                      f=conjunction_truth_value.frequency,
                                                      c=conjunction_truth_value.confidence)
        self.quadtree_id = self.quadtree_id + 1

        for quad_child in quad_tree.children:
            sentence = quad_child.value
            spatial_conjunction.stamp.evidential_base.merge_sentence_evidential_base_into_self(sentence)

        return spatial_conjunction




class TemporalModule(ItemContainer):
    """
        Performs
            temporal composition
                and
            anticipation (negative evidence for predictive implications)
    """

    def __init__(self, NARS, item_type, capacity):
        ItemContainer.__init__(self, item_type=item_type, capacity=capacity)

        self.NARS = NARS
        # temporal chaining
        self.temporal_chain = []

        # anticipation
        self.anticipations_queue = []
        self.current_anticipation = None

    def __len__(self):
        return len(self.temporal_chain)

    def __iter__(self):
        return iter(self.temporal_chain)

    def __getitem__(self, index):
        return self.temporal_chain[index]

    def PUT_NEW(self, object):
        """
            Put the newest item onto the end of the buffer.
        """
        assert (isinstance(object, self.item_type)), "item object must be of type " + str(self.item_type)

        item = Item(object, self.get_next_item_id())
        self._put_into_lookup_dict(item)  # Item Container

        # add to buffer
        self.temporal_chain.append(item)

        # update temporal chain
        if len(self.temporal_chain) > self.capacity:
            popped_item = self.temporal_chain.pop(0)
            ItemContainer._take_from_lookup_dict(self, popped_item.key)

        self.process_temporal_chaining()


    def process_temporal_chaining(self):
        if len(self) > 0:
            self.temporal_chaining_2_conjunction()
            self.temporal_chaining_2_imp()

    def get_most_recent_event_task(self):
        return self.temporal_chain[-1]

    def temporal_chaining_2_imp(self):
        """
            Perform temporal chaining

            produce all possible forward implication statements using temporal induction and intersection
                A =/> B

            for the latest statement in the chain
        """
        NARS = self.NARS
        temporal_chain = self.temporal_chain
        num_of_events = len(temporal_chain)

        event_task_B = self.get_most_recent_event_task().object
        event_B = event_task_B.sentence

        if not isinstance(event_B.statement, NALGrammar.Terms.StatementTerm): return #todo remove this. temporarily prevent arrays in postconditions

        def process_sentence(derived_sentence):
            if derived_sentence is not None:
                if NARS is not None:
                    task = Task(derived_sentence)
                    NARS.global_buffer.PUT_NEW(task)

        # produce all possible forward implication statements using temporal induction and intersection
        # A &/ B,
        # A =/> B
        for i in range(0,num_of_events-1):  # and do induction with events occurring afterward
            event_task_A = temporal_chain[i].object
            event_A = event_task_A.sentence

            if not (isinstance(event_A.statement, NALGrammar.Terms.CompoundTerm)
                    and NALSyntax.TermConnector.is_conjunction(event_A.statement.connector)
                    and isinstance(event_A.statement.subterms[0], NALGrammar.Terms.CompoundTerm)
                    and NALSyntax.TermConnector.is_conjunction(event_A.statement.subterms[0].connector)): continue

            derived_sentences = NARSInferenceEngine.do_temporal_inference_two_premise(event_A, event_B)

            for derived_sentence in derived_sentences:
                if not isinstance(derived_sentence.statement, NALGrammar.Terms.StatementTerm): continue  # only implications
                process_sentence(derived_sentence)

    def temporal_chaining_2_conjunction(self):
        """
            Perform temporal chaining

            produce all possible forward implication statements using temporal induction and intersection
                A && B

            for the latest statement in the chain
        """
        NARS = self.NARS
        temporal_chain = self.temporal_chain
        num_of_events = len(temporal_chain)

        event_task_B = self.get_most_recent_event_task().object
        event_B = event_task_B.sentence

        if not (isinstance(event_B.statement, NALGrammar.Terms.CompoundTerm)
                and NALSyntax.TermConnector.is_conjunction(event_B.statement.connector)
                and (isinstance(event_B.statement.subterms[0], NALGrammar.Terms.SpatialTerm) or isinstance(event_B.statement.subterms[0], NALGrammar.Terms.StatementTerm))): return

        def process_sentence(derived_sentence):
            if derived_sentence is not None:
                if NARS is not None:
                    task = Task(derived_sentence)
                    NARS.global_buffer.PUT_NEW(task)

        # A &/ B
        for i in range(0,num_of_events-1):
            event_task_A = temporal_chain[i].object
            event_A = event_task_A.sentence

            if not (isinstance(event_A.statement, NALGrammar.Terms.CompoundTerm)
                    and NALSyntax.TermConnector.is_conjunction(event_A.statement.connector)
                    and (isinstance(event_A.statement.subterms[0], NALGrammar.Terms.SpatialTerm) or isinstance(
                        event_A.statement.subterms[0], NALGrammar.Terms.StatementTerm))): return

            derived_sentences = NARSInferenceEngine.do_temporal_inference_two_premise(event_A, event_B)

            for derived_sentence in derived_sentences:
                if isinstance(derived_sentence.statement, NALGrammar.Terms.StatementTerm): continue  # only conjunctions
                process_sentence(derived_sentence)

    def temporal_chaining_3_conjunction(self):
        """
            Perform temporal chaining

            produce all possible forward implication statements using temporal induction and intersection
                A && B && C

            for the latest statement in the chain
        """
        NARS = self.NARS
        temporal_chain = self.temporal_chain
        num_of_events = len(temporal_chain)

        event_task_C = self.get_most_recent_event_task().object
        event_C = event_task_C.sentence

        if not isinstance(event_C.statement, NALGrammar.Terms.SpatialTerm): return

        def process_sentence(derived_sentence):
            if derived_sentence is not None:
                if NARS is not None:
                    task = Task(derived_sentence)
                    NARS.global_buffer.PUT_NEW(task)


        for i in range(0, num_of_events - 1):  # and do induction with events occurring afterward
            event_task_A = temporal_chain[i].object
            event_A = event_task_A.sentence

            if not isinstance(event_A.statement,
                          NALGrammar.Terms.SpatialTerm) or event_A.statement == event_C.statement: continue

            for j in range(i + 1, num_of_events - 1):
                event_task_B = temporal_chain[j].object
                event_B = event_task_B.sentence

                if not isinstance(event_B.statement, NALGrammar.Terms.SpatialTerm) \
                    or event_B.statement == event_A.statement \
                    or event_B.statement == event_C.statement: continue

                result_statement = NALGrammar.Terms.CompoundTerm([event_A.statement,
                                                                  event_B.statement,
                                                                  event_C.statement],
                                                                 NALSyntax.TermConnector.Conjunction)

                truth_value = NALInferenceRules.TruthValueFunctions.F_Intersection(event_A.value.frequency,
                                                                     event_A.value.confidence,
                                                                     event_B.value.frequency,
                                                                     event_B.value.confidence)

                truth_value = NALInferenceRules.TruthValueFunctions.F_Intersection(truth_value.frequency,
                                                                     truth_value.confidence,
                                                                     event_C.value.frequency,
                                                                     event_C.value.confidence)

                truth_value = NALGrammar.Values.TruthValue(frequency=truth_value.frequency,
                                                     confidence=truth_value.confidence)
                result = NALGrammar.Sentences.Judgment(statement=result_statement,
                                                       value=truth_value,
                                                       occurrence_time=Global.Global.get_current_cycle_number())

                process_sentence(result)

    def temporal_chaining_3(self):
        """
            Perform temporal chaining

            produce all possible forward implication statements using temporal induction and intersection
                A &/ B,
                A =/> B
                and
                (A &/ B) =/> C

            for the latest statement in the chain
        """

        NARS = self.NARS
        temporal_chain = self.temporal_chain
        num_of_events = len(temporal_chain)

        event_task_C = self.get_most_recent_event_task().object
        event_C = event_task_C.sentence

        def process_sentence(derived_sentence):
            if derived_sentence is not None:
                if NARS is not None:
                    task = Task(derived_sentence)
                    NARS.global_buffer.PUT_NEW(task)

        # produce all possible forward implication statements using temporal induction and intersection
        # A &/ C,
        # A =/> C
        # and
        # (A &/ B) =/> C

        for i in range(0, num_of_events - 1):  # and do induction with events occurring afterward
            event_task_A = temporal_chain[i].object
            event_A = event_task_A.sentence

            if not isinstance(event_A.statement,
                          NALGrammar.Terms.SpatialTerm): continue  # todo remove this eventually. only arrays in precondition

            # produce statements (A =/> C) and (A &/ C)
            if isinstance(event_C.statement,
                              NALGrammar.Terms.SpatialTerm):
                derived_sentences = NARSInferenceEngine.do_temporal_inference_two_premise(event_A, event_C)

                for derived_sentence in derived_sentences:
                    if isinstance(derived_sentence.statement, NALGrammar.Terms.StatementTerm): continue  # ignore simple implications
                    process_sentence(derived_sentence) #todo A_C conjunction only


            for j in range(i + 1, num_of_events - 1):
                event_task_B = temporal_chain[j].object
                event_B = event_task_B.sentence

                conjunction_A_B = NALInferenceRules.Temporal.TemporalIntersection(event_A,
                                                                                  event_B)  # (A &/ B)

                if conjunction_A_B is not None:
                    derived_sentence = NALInferenceRules.Temporal.TemporalInduction(conjunction_A_B,
                                                                                    event_C)  # (A &/ B) =/> C
                    process_sentence(derived_sentence)


    def temporal_chaining_4(self):
        """
            Perform temporal chaining

            produce all possible forward implication statements using temporal induction and intersection
                A &/ D,
                A =/> D
                and
                (A &/ B) =/> D
                (A &/ C) =/> D
                and
                (A &/ B &/ C) =/> D

            for the latest event D in the chain

            todo not supported
        """
        NARS = self.NARS
        results = []
        temporal_chain = self.temporal_chain
        num_of_events = len(temporal_chain)

        event_task_D = self.get_most_recent_event_task()
        event_D = event_task_D.sentence

        def process_sentence(derived_sentence):
            if derived_sentence is not None:
                results.append(derived_sentence)
                if NARS is not None:
                    task = Task(derived_sentence)
                    NARS.global_buffer.PUT_NEW(task)

        # produce all possible forward implication statements using temporal induction and intersection
        # A &/ C,
        # A =/> C
        # and
        # (A &/ B) =/> C
        for i in range(0, num_of_events - 1):  # and do induction with events occurring afterward
            event_task_A = temporal_chain[i].object
            event_A = event_task_A.sentence

            # produce statements (A =/> D) and (A &/ D)
            derived_sentences = NARSInferenceEngine.do_temporal_inference_two_premise(event_A, event_D)

            for derived_sentence in derived_sentences:
                # if isinstance(derived_sentence.statement, NALGrammar.Terms.StatementTerm): continue
                process_sentence(derived_sentence)

            for j in range(i + 1, num_of_events - 1):
                event_task_B = temporal_chain[j].object
                event_B = event_task_B.sentence

                conjunction_A_B = NALInferenceRules.Temporal.TemporalIntersection(event_A,
                                                                                  event_B)  # (A &/ B)
                if conjunction_A_B is not None:
                    derived_sentence = NALInferenceRules.Temporal.TemporalInduction(conjunction_A_B,
                                                                                    event_D)  # (A &/ B) =/> D
                    process_sentence(derived_sentence)

                for k in range(j + 1, num_of_events - 1):
                    if conjunction_A_B is None: break
                    event_task_C = temporal_chain[k].object
                    event_C = event_task_C.sentence
                    conjunction_A_B_C = NALInferenceRules.Temporal.TemporalIntersection(conjunction_A_B,
                                                                                        event_C)  # (A &/ B &/ C)
                    derived_sentence = NALInferenceRules.Temporal.TemporalInduction(conjunction_A_B_C,
                                                                                    event_D)  # (A &/ B &/ C) =/> D
                    process_sentence(derived_sentence)

        return results

    def anticipate_from_event(self, observed_event):
        """
            # form new anticipation from observed event
        """
        return #todo

        random_prediction = self.NARS.memory.get_random_bag_prediction(observed_event)

        if random_prediction is not None:
            # something is anticipated
            self.anticipate_from_concept(self.NARS.memory.peek_concept(random_prediction.statement),
                                         random_prediction)


    def anticipate_from_concept(self, higher_order_anticipation_concept, best_belief=None):
        """
            Form an anticipation based on a higher-order concept.
            Uses the best belief from the belief table, unless one is provided.

        :param higher_order_anticipation_concept:
        :param best_belief:
        :return:
        """
        return #todo
        if best_belief is None:
            best_belief = higher_order_anticipation_concept.belief_table.peek()

        expectation = best_belief.get_expectation()

        # use this for 1 anticipation only
        # if self.current_anticipation is not None:
        #     # in the middle of a operation sequence already
        #     current_anticipation_expectation = self.current_anticipation
        #     if expectation <= current_anticipation_expectation: return # don't execute since the current anticipation is more expected
        #     # else, the given operation is more expected
        #     self.anticipations_queue.clear()

        self.current_anticipation = expectation

        working_cycles = NALInferenceRules.HelperFunctions.convert_from_interval(
            higher_order_anticipation_concept.term.interval)

        postcondition = higher_order_anticipation_concept.term.get_predicate_term()
        self.anticipations_queue.append([working_cycles, higher_order_anticipation_concept, postcondition])
        if Config.DEBUG: Global.Global.debug_print(
            str(postcondition) + " IS ANTICIPATED FROM " + str(best_belief) + " Total Anticipations:" + str(
                len(self.anticipations_queue)))

    def process_anticipations(self):
        """

            anticipation (negative evidence for predictive implications)
        """
        return #todo
        # process pending anticipations
        i = 0

        while i < len(self.anticipations_queue):
            remaining_cycles, best_prediction_concept, anticipated_postcondition = self.anticipations_queue[
                i]  # event we expect to occur
            anticipated_postcondition_concept = self.NARS.memory.peek_concept(anticipated_postcondition)
            if remaining_cycles == 0:
                if anticipated_postcondition_concept.is_positive():
                    # confirmed
                    if Config.DEBUG: Global.Global.debug_print(
                        str(anticipated_postcondition_concept) + " SATISFIED - CONFIRMED ANTICIPATION" + str(
                            best_prediction_concept.term))
                else:
                    sentence = NALGrammar.Sentences.Judgment(statement=best_prediction_concept.term,
                                                             value=NALGrammar.Values.TruthValue(frequency=0.0,
                                                                                                confidence=Config.DEFAULT_DISAPPOINT_CONFIDENCE))
                    if Config.DEBUG:
                        Global.Global.debug_print(str(
                            anticipated_postcondition_concept) + " DISAPPOINT - FAILED ANTICIPATION, NEGATIVE EVIDENCE FOR " + str(
                            sentence))
                    self.NARS.global_buffer.PUT_NEW(Task(sentence))
                self.anticipations_queue.pop(i)
                self.current_anticipation = None
                i -= 1
            else:
                self.anticipations_queue[i][0] -= 1

            i += 1
