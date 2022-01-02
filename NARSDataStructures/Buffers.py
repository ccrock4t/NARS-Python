"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import math
import timeit as time

import Config
import Global
import NALSyntax
import NARSInferenceEngine
from NARSDataStructures.Bag import Bag
from NARSDataStructures.ItemContainers import ItemContainer, Item
from NARSDataStructures.Other import Depq, Task
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

    def put_new(self, object):
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

    def __init__(self, dimensions):
        """
        :param dimensions: dimensions of the 2d buffer as a tuple (y, x)
        """
        assert len(dimensions) == 2, "ERROR: Spatial buffer only support 2D structures"
        self.dimensions = dimensions
        self.array = np.full(shape=dimensions,
                             fill_value=NALGrammar.Sentences.TruthValue(0.0,0.9))
        self.components_bag = Bag(item_type=tuple,
                                  capacity=1000)
        self.last_taken_img_array = None

        # initialize with uniform probabilility
        for indices, truth_value in np.ndenumerate(self.array):
            item = self.components_bag.put_new(indices)
            self.components_bag.change_priority(item.key, 0.5)

    def blank_image(self):
        self.set_image(np.empty(shape=self.array.shape))

    def set_image(self, img):
        self.img = img
        truth_array = self.transduce_raw_vision_array(img)
        self._set_array(array=truth_array)


    def _set_array(self, array):
        """
            Set all elements of the spatial buffer.
            All of the current elements are removed.

            :param array: array of truth-values representing sensation signal values in a topographical mapping
        """
        assert array.shape == self.dimensions,\
            "ERROR: Data dimensions are incompatible with Spatial Buffer dimensions " \
            + str(array.shape) + " and " + str(self.dimensions)

        self.array = array
        self.components_bag.clear()
        for indices, truth_value in np.ndenumerate(array):
            e = NALInferenceRules.TruthValueFunctions.Expectation(truth_value.frequency,
                                                                         truth_value.confidence)
            priority = 2*abs(e - 0.5)
            self.components_bag.put_new(indices)
            self.components_bag.change_priority(Item.get_key_from_object(indices), priority)




    def take(self):
        """
            Probabilistically select a spatial subset of the buffer.
            :return: an Array Judgment of the selected subset.
        """
        # probabilistically peek the 2 vertices of the box
        item1 = self.components_bag.peek()
        item2 = self.components_bag.peek()

        # get their indices
        element1_idx_y, element1_idx_x = item1.object
        element2_idx_y, element2_idx_x = item2.object

        min_x, min_y = min(element1_idx_x, element2_idx_x), min(element1_idx_y, element2_idx_y)
        max_x, max_y = max(element1_idx_x, element2_idx_x), max(element1_idx_y, element2_idx_y)

        # min_x, min_y = 0,0
        # max_x, max_y = 28,28

        # extract subset of elements inside the bounding box (inclusive)
        truth_val_subset = self.array[min_y:max_y+1, min_x:max_x+1]

        # create the common predicat
        predicate_name = 'BRIGHT'
        predicate_term = NALGrammar.Terms.AtomicTerm(term_string=predicate_name)

        # create a higher-order compound of the extracted subset
        array_truth_value = None
        elements_array = np.empty(shape=truth_val_subset.shape,
                                  dtype=NALGrammar.Terms.Term)
        for indices,element in np.ndenumerate(truth_val_subset):
            y, x = indices
            y, x = int(y), int(x)
            truth_value = truth_val_subset[y, x]
            expectation = NALInferenceRules.TruthValueFunctions.Expectation(truth_value.frequency,
                                                                            truth_value.confidence)
            subject_name = str(y) + "_" + str(x)
            positive_statement = NALGrammar.Terms.from_string("("+ subject_name + "-->" + predicate_name + ")")

            if expectation > Config.POSITIVE_THRESHOLD:
                element = positive_statement
            else:
                element = NALGrammar.Terms.CompoundTerm([positive_statement],
                                                          term_connector=NALSyntax.TermConnector.Negation)
                truth_value = NALInferenceRules.TruthValueFunctions.F_Negation(truth_value.frequency,
                                                                              truth_value.confidence)

            if array_truth_value is None:
                array_truth_value = truth_value
            else:
                array_truth_value = NALInferenceRules.TruthValueFunctions.F_Revision(array_truth_value.frequency,
                                               array_truth_value.confidence,
                                               truth_value.frequency,
                                               truth_value.confidence)
            elements_array[indices] = element


        statement = NALGrammar.Terms.SpatialTerm(spatial_subterms=elements_array,
                                                 center=(min_x,min_y))

        # create a corresponding judgment with the compound
        array_judgment = NALGrammar.Sentences.Judgment(statement=statement,
                                                      value=array_truth_value,
                                                       occurrence_time=Global.Global.get_current_cycle_number())

        last_taken_img_array = np.zeros(shape=self.img.shape)
        last_taken_img_array[min_y:max_y+1, min_x:max_x+1] = self.img[min_y:max_y+1, min_x:max_x+1]
        self.last_taken_img_array = last_taken_img_array  # store for visualization
        return array_judgment

    def transduce_raw_vision_array(self, img_array):
        """
            Transduce raw vision data into NARS truth-values
            :param img_array:
            :return: python array of NARS truth values, with the same dimensions as given raw data
        """
        # fft_array = np.fft.fft2(img_array)
        # fshift = np.fft.fftshift(fft_array)
        # magnitude_spectrum = 20 * np.log(np.abs(fshift))

        max_value = 255

        def create_2d_truth_value_array(*indices):

            focus = Config.FOCUS # higher focus means confidence dropoff in periphery occurs faster.
            coords = tuple([int(var) for var in indices])
            y,x = coords
            pixel_value = float(img_array[y, x])

            f = pixel_value / max_value
            if f > 1: f = 1

            relative_indices = []
            offsets = (img_array.shape[0]-1)/2, (img_array.shape[1]-1)/2
            for i in range(2):
                relative_indices.append((indices[i] - offsets[i]) / offsets[i])

            unit = NALInferenceRules.HelperFunctions.get_unit_evidence()
            c = unit*math.exp(-1*((relative_indices[0]**2 / (focus**2)) + (relative_indices[1]**2 / (focus**2))))

            return NALGrammar.Sentences.TruthValue(f, c)

        func_vectorized = np.vectorize(create_2d_truth_value_array)
        truth_value_array = np.fromfunction(function=func_vectorized,
                                            shape=img_array.shape)

        return truth_value_array


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

    def put_new(self, object):
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
            self.temporal_chaining_2()

    def get_most_recent_event_task(self):
        return self.temporal_chain[-1]

    def temporal_chaining_2(self):
        """
            Perform temporal chaining

            produce all possible forward implication statements using temporal induction and intersection
                A =/> B

            for the latest statement in the chain
        """
        NARS = self.NARS
        results = []
        temporal_chain = self.temporal_chain
        num_of_events = len(temporal_chain)

        event_task_B = self.get_most_recent_event_task().object
        event_B = event_task_B.sentence

        if isinstance(event_B.statement, NALGrammar.Terms.SpatialTerm): return #todo remove this. temporarily prevent arrays in postconditions

        def process_sentence(derived_sentence):
            if derived_sentence is not None:
                results.append(derived_sentence)
                if NARS is not None:
                    task = Task(derived_sentence)
                    NARS.global_buffer.put_new(task)

        # produce all possible forward implication statements using temporal induction and intersection
        # A &/ B,
        # A =/> B
        for i in range(0,num_of_events-1):  # and do induction with events occurring afterward
            event_task_A = temporal_chain[i].object
            event_A = event_task_A.sentence

            if not isinstance(event_A.statement, NALGrammar.Terms.SpatialTerm): continue #todo remove. Only allow arrays in preconditions

            derived_sentences = NARSInferenceEngine.do_temporal_inference_two_premise(event_A, event_B)

            for derived_sentence in derived_sentences:
                # if isinstance(derived_sentence.statement, NALGrammar.Terms.StatementTerm): continue  # ignore simple implications
                process_sentence(derived_sentence)

        return results


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
        if not self.temporal_chain_has_changes: return []
        NARS = self.NARS
        results = []
        temporal_chain = self.temporal_chain
        num_of_events = len(temporal_chain)

        event_task_C = self.get_most_recent_event_task()
        event_C = event_task_C.sentence

        def process_sentence(derived_sentence):
            if derived_sentence is not None:
                results.append(derived_sentence)
                if NARS is not None:
                    task = Task(derived_sentence)
                    NARS.global_buffer.put_new(task)

        # produce all possible forward implication statements using temporal induction and intersection
        # A &/ C,
        # A =/> C
        # and
        # (A &/ B) =/> C
        for i in range(0, num_of_events - 1):  # and do induction with events occurring afterward
            event_task_A = temporal_chain[i].object
            event_A = event_task_A.sentence

            # produce statements (A =/> C) and (A &/ C)
            derived_sentences = NARSInferenceEngine.do_temporal_inference_two_premise(event_A, event_C)

            for derived_sentence in derived_sentences:
                # if isinstance(derived_sentence.statement, NALGrammar.Terms.StatementTerm): continue  # ignore simple implications
                process_sentence(derived_sentence)

            for j in range(i + 1, num_of_events - 1):
                event_task_B = temporal_chain[j].object
                event_B = event_task_B.sentence

                conjunction_A_B = NALInferenceRules.Temporal.TemporalIntersection(event_A,
                                                                                  event_B)  # (A &/ B)

                if conjunction_A_B is not None:
                    derived_sentence = NALInferenceRules.Temporal.TemporalInduction(conjunction_A_B,
                                                                                    event_C)  # (A &/ B) =/> C
                    process_sentence(derived_sentence)

        self.temporal_chain_has_changes = False

        return results

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
        if not self.temporal_chain_has_changes: return []
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
                    NARS.global_buffer.put_new(task)

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

        self.temporal_chain_has_changes = False

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
                    self.NARS.global_buffer.put_new(Task(sentence))
                self.anticipations_queue.pop(i)
                self.current_anticipation = None
                i -= 1
            else:
                self.anticipations_queue[i][0] -= 1

            i += 1
