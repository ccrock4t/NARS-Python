"""
    Author: Christian Hahm
    Created: December 24, 2020
    Purpose: Holds data structure implementations that are specific / custom to NARS
"""
import math
import random
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

    def __init__(self, dimensions):
        """
        :param dimensions: dimensions of the 2d buffer as a tuple (y, x)
        """
        assert len(dimensions) == 2, "ERROR: Spatial buffer only support 2D structures"
        self.dimensions = dimensions
        self.array = np.full(shape=dimensions,
                             fill_value=NALGrammar.Sentences.TruthValue(0.0,0.9))
        self.components_bag = Bag(item_type=object,
                                  capacity=1000,
                                  granularity=100)

        self.pooled_array = np.full(shape=dimensions,
                             fill_value=NALGrammar.Sentences.TruthValue(0.0,0.9))
        self.pooled_components_bag = Bag(item_type=object,
                                  capacity=1000,
                                  granularity=100)

        self.last_taken_img_array = None
        self.last_sentence = None

        # initialize with uniform probabilility

    def blank_image(self):
        self.set_image(np.empty(shape=self.array.shape))

    def set_image(self, img):
        self.img = img
        original_event_array = self.transduce_raw_vision_array(img)

        # assert event_array.shape == self.dimensions,\
        #     "ERROR: Data dimensions are incompatible with Spatial Buffer dimensions " \
        #     + str(event_array.shape) + " and " + str(self.dimensions)

        self.array = self.create_pooled_sensation_array(original_event_array, stride=1)
        self.components_bag.clear()

        maximum = 0
        for indices, sentence in np.ndenumerate(self.array):
            if sentence.value.frequency > Config.POSITIVE_THRESHOLD \
                    and not (isinstance(sentence.statement,
                                        NALGrammar.Terms.CompoundTerm) and sentence.statement.connector == NALSyntax.TermConnector.Negation):
                maximum = max(maximum, sentence.value.frequency * sentence.value.confidence)

        for indices, sentence in np.ndenumerate(self.array):
            if sentence.value.frequency > Config.POSITIVE_THRESHOLD \
                and not (isinstance(sentence.statement,NALGrammar.Terms.CompoundTerm) and sentence.statement.connector == NALSyntax.TermConnector.Negation):
                priority = sentence.value.frequency * sentence.value.confidence / maximum
                object = indices
                self.components_bag.PUT_NEW(object)
                self.components_bag.change_priority(Item.get_key_from_object(object), priority)



        # pooled
        self.pooled_array = self.create_pooled_sensation_array(original_event_array, stride=2)
        #self.pooled_array = self.create_pooled_sensation_array(self.pooled_array , stride=2)
        self.pooled_components_bag.clear()

        maximum = 0
        for indices, sentence in np.ndenumerate(self.pooled_array):
            if sentence.value.frequency > Config.POSITIVE_THRESHOLD \
                    and not (isinstance(sentence.statement,
                                        NALGrammar.Terms.CompoundTerm) and sentence.statement.connector == NALSyntax.TermConnector.Negation):
                maximum = max(maximum, sentence.value.frequency * sentence.value.confidence)

        for indices, sentence in np.ndenumerate(self.pooled_array):
            if sentence.value.frequency > Config.POSITIVE_THRESHOLD \
                    and not (isinstance(sentence.statement,
                                        NALGrammar.Terms.CompoundTerm) and sentence.statement.connector == NALSyntax.TermConnector.Negation):
                priority = sentence.value.frequency * sentence.value.confidence / maximum
                object = indices
                self.pooled_components_bag.PUT_NEW(object)
                self.pooled_components_bag.change_priority(Item.get_key_from_object(object), priority)

    def take(self, pooled):
        """
            Probabilistically select a spatial subset of the buffer.
            :return: an Array Judgment of the selected subset.
        """
        if pooled:
            bag = self.pooled_components_bag
            array = self.pooled_array
        else:
            bag = self.components_bag
            array = self.array

        # probabilistically peek the 2 vertices of the box
        # selection 1: small fixed windows

        indices = bag.peek()
        if indices is None: return None

        y, x = indices.object
        radius = 1#random.randint(1,2)
        min_x, min_y = max(x - radius, 0), max(y - radius, 0)
        max_x, max_y = min(x + radius, array.shape[1] - 1), min(y + radius,
                                                                                 array.shape[0] - 1)

        extracted = array[min_y:max_y+1, min_x:max_x+1]
        sentence_subset= []
        for idx,sentence in np.ndenumerate(extracted):
            if not (isinstance(sentence.statement, NALGrammar.Terms.CompoundTerm)
                and sentence.statement.connector == NALSyntax.TermConnector.Negation):
                sentence_subset.append(sentence)

        total_truth = None
        statement_subset = []
        for sentence in sentence_subset:
            if total_truth is None:
                total_truth = sentence.value
            else:
                total_truth = NALInferenceRules.TruthValueFunctions.F_Intersection(sentence.value.frequency,
                                                                     sentence.value.confidence,
                                                                     total_truth.frequency,
                                                                     total_truth.confidence)
            statement_subset.append(sentence.statement)


        # create conjunction of features
        statement = NALGrammar.Terms.CompoundTerm(subterms=statement_subset,
                                                  term_connector=NALSyntax.TermConnector.Conjunction)

        event_sentence = NALGrammar.Sentences.Judgment(statement=statement,
                                      value=total_truth,
                                      occurrence_time=Global.Global.get_current_cycle_number())


        # last_taken_img_array = np.zeros(shape=self.img.shape)
        # last_taken_img_array[min_y+1:(max_y+1)+1, min_x+1:(max_x+1)+1] = self.img[min_y+1:(max_y+1)+1, min_x+1:(max_x+1)+1]
        # self.last_taken_img_array = last_taken_img_array  # store for visualization

        return event_sentence

    def create_spatial_conjunction(self, subset):
        """

        :param subset: 2d Array of positive (non-negated) sentences / events
        :return:
        """
        conjunction_truth_value = None
        terms_array = np.empty(shape=subset.shape,
                               dtype=NALGrammar.Terms.Term)
        for indices, sentence in np.ndenumerate(subset):
            truth_value = sentence.value
            term = sentence.statement

            if conjunction_truth_value is None:
                conjunction_truth_value = truth_value
            else:
                conjunction_truth_value = NALInferenceRules.TruthValueFunctions.F_Intersection(conjunction_truth_value.frequency,
                                               conjunction_truth_value.confidence,
                                               truth_value.frequency,
                                               truth_value.confidence)

            terms_array[indices] = term

        spatial_conjunction_term = NALGrammar.Terms.SpatialTerm(spatial_subterms=terms_array,
                                                                connector=NALSyntax.TermConnector.ArrayConjunction)
        spatial_conjunction = NALGrammar.Sentences.Judgment(statement=spatial_conjunction_term,
                                      value=conjunction_truth_value,
                                      occurrence_time=Global.Global.get_current_cycle_number())

        return spatial_conjunction

    def create_pooled_sensation_array(self, array, stride):
        """
            Takes an array of events, and returns an array of events except 2x2 pooled with stride
        :param array:
        :param stride:
        :return:
        """
        pad_sentence = Global.Global.ARRAY_NEGATIVE_SENTENCE
        stride_original_sentences = np.empty(shape=(2,2),
                                             dtype=NALGrammar.Sentences.Sentence)
        if stride == 1:
            pool_terms_array = np.empty(shape=(array.shape[0] - 1, array.shape[1] - 1),
                                      dtype=NALGrammar.Terms.Term)
        elif stride == 2:
            height = array.shape[0] // 2 if array.shape[0] % 2 == 0 else (array.shape[0]+1) // 2
            width = array.shape[1] // 2 if array.shape[1] % 2 == 0 else (array.shape[1]+1) // 2
            pool_terms_array = np.empty(shape=(height, width), dtype=NALGrammar.Terms.Term)
        else:
            assert False,"ERROR: Does not support stride > 2"

        for indices,sentence in np.ndenumerate(array):
            y, x = indices
            y, x = int(y), int(x)
            if stride == 2 and not (x % 2 == 0 or y % 2 == 0): continue # only use even indices for stride 2

            pool_y = y // 2 if stride == 2 else y
            pool_x = x // 2 if stride == 2 else x

            # pool sensation
            if y < array.shape[0] - 1 and x < array.shape[1] - 1:
                # not last column or row yet
                stride_original_sentences = np.array(array[y:y+2, x:x+2])  # get 4x4

            elif y == array.shape[0] - 1 and x < array.shape[1] - 1:
                # last row, not last column
                if stride == 1: continue
                stride_original_sentences[0,:] = np.array([array[y, x], array[y, x+1]])
                stride_original_sentences[1,:] = np.array([pad_sentence, pad_sentence])

            elif y < array.shape[0] - 1 and x == array.shape[1] - 1:
                # last column, not last row
                if stride == 1: continue
                stride_original_sentences[0,:] = np.array([array[y, x], pad_sentence])
                stride_original_sentences[1,:] = np.array([array[y+1, x], pad_sentence])

            elif y == array.shape[0] - 1 and x == array.shape[1] - 1:
                if stride == 1: continue
                #last row and column
                stride_original_sentences[0, :] = np.array([array[y, x], pad_sentence])
                stride_original_sentences[1, :] = np.array([pad_sentence, pad_sentence])

            pool_terms_array[pool_y, pool_x] = self.create_spatial_disjunction(np.array(stride_original_sentences))

        return pool_terms_array

    def create_spatial_disjunction(self, array_of_events):
        """

        :param terms: 2x2 Array of positive (non-negated) sentences / events
        :param terms_array: 2x2 array of potentially negated Terms
        :return:
        """
        #TODO FINISH THIS
        all_negative = True
        for i,event in np.ndenumerate(array_of_events):
            all_negative = all_negative \
                           and (isinstance(event.statement, NALGrammar.Terms.CompoundTerm) and event.statement.connector == NALSyntax.TermConnector.Negation)

        disjunction_truth = None
        disjunction_subterms = np.empty(shape=array_of_events.shape,
                                  dtype=NALGrammar.Terms.Term)

        for indices, event in np.ndenumerate(array_of_events):
            if isinstance(event.statement, NALGrammar.Terms.CompoundTerm) \
                    and event.statement.connector == NALSyntax.TermConnector.Negation:
                # negated event, get positive
                truth_value = NALInferenceRules.TruthValueFunctions.F_Negation(event.value.frequency,
                                                                 event.value.confidence) # get regular positive back
                new_statement = event.statement.subterms[0]
            else:
                # already positive
                truth_value = event.value
                new_statement = event.statement

            disjunction_subterms[indices] = new_statement

            if disjunction_truth is None:
                disjunction_truth = truth_value
            else:
                # OR
                disjunction_truth = NALInferenceRules.TruthValueFunctions.F_Union(disjunction_truth.frequency,
                                                                                  disjunction_truth.confidence,
                                                                                  truth_value.frequency,
                                                                                  truth_value.confidence)

        disjunction_term = NALGrammar.Terms.SpatialTerm(spatial_subterms=disjunction_subterms,
                                                                connector=NALSyntax.TermConnector.ArrayDisjunction)

        if all_negative:
            disjunction_truth = NALInferenceRules.TruthValueFunctions.F_Negation(disjunction_truth.frequency,
                                                                           disjunction_truth.confidence)
            disjunction_term = NALGrammar.Terms.CompoundTerm(subterms=[disjunction_term],
                                                            term_connector=NALSyntax.TermConnector.Negation)


        spatial_disjunction = NALGrammar.Sentences.Judgment(statement=disjunction_term,
                                      value=disjunction_truth)

        return spatial_disjunction

    def transduce_raw_vision_array(self, img_array):
        """
            Transduce raw vision data into NARS truth-values
            :param img_array:
            :return: python array of NARS truth values, with the same dimensions as given raw data
        """
        max_value = 255

        def create_2d_truth_value_array(*indices):
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
            c = unit*math.exp(-1*((Config.FOCUSY ** 2)*(relative_indices[0]**2) + (Config.FOCUSX ** 2)*(relative_indices[1]**2)))

            predicate_name = 'B'
            subject_name = str(y) + "_" + str(x)


            if f > Config.POSITIVE_THRESHOLD:
                truth_value = NALGrammar.Sentences.TruthValue(f, c)
                statement = NALGrammar.Terms.from_string("(" + subject_name + "-->" + predicate_name + ")")
            else:
                truth_value = NALGrammar.Sentences.TruthValue(NALInferenceRules.ExtendedBooleanOperators.bnot(f), c)
                statement = NALGrammar.Terms.from_string("(--,(" + subject_name + "-->" + predicate_name + "))")

            # create the common predicate

            return NALGrammar.Sentences.Judgment(statement=statement,
                                                       value=truth_value)


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
        if Config.Testing: return
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

            if Config.Testing or not isinstance(event_C.statement,
                              NALGrammar.Terms.StatementTerm): continue  # todo remove this. temporarily prevent arrays in postconditions


            for j in range(i + 1, num_of_events - 1):
                event_task_B = temporal_chain[j].object
                event_B = event_task_B.sentence

                if not isinstance(event_B.statement,
                                  NALGrammar.Terms.SpatialTerm): continue  # todo remove this eventually. only arrays in precondition

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
