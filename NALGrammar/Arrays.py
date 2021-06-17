"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Enforces Narsese grammar that is used throughout the project
"""

import numpy as np

import Config
import Global
import NALGrammar
import NALSyntax


class Array():
    def __init__(self, dimensions, truth_values = None, occurrence_time=None):
        """
        :param parent: Name of the array term
        :param dimensions: the number of elements in each dimensional axis (x,y,z);
            provides a granularity = 2.0/(dim_length - 1)
        """
        self.is_array = dimensions is not None
        self.truth_values = None
        if not self.is_array: return
        self.truth_values = np.array(truth_values)
        self.dimensions = dimensions
        self.num_of_dimensions = len(dimensions)
        assert self.num_of_dimensions <= 3, "ERROR: Does not support more than 3 dimensions"
        assert self.num_of_dimensions > 0, "ERROR: Use Atomic Term instead of zero-dimensional array"

        self.dim_lengths = dimensions
        self.offsets = []
        for i in range(self.num_of_dimensions):
            self.offsets.append((dimensions[i] - 1) / 2.0)

        # prepare to store an image if necessary
        self.element_string_array = None
        if Global.Global.gui_use_internal_data and (isinstance(self, NALGrammar.Sentences.Judgment) or isinstance(self, NALGrammar.Sentences.Goal)):
            self.image_array = np.empty(shape=dimensions,dtype=np.uint8) # image_array is used to visualize an array of judgments/goals activations
            self.image_alpha_array = np.empty(shape=dimensions,
                                        dtype=np.uint8)  # image_array is used to visualize an array of judgments/goals activations
            if Config.ARRAY_SENTENCES_DRAW_INDIVIDUAL_ELEMENTS:
                self.element_string_array = np.empty(shape=dimensions,dtype=object)
        else:
            self.image_array = None

        vectorized_func = np.vectorize(array_index_function)
        self.array = np.fromfunction(function=vectorized_func,shape=dimensions,self_obj=self,occurrence_time=occurrence_time)


    def __getitem__(self, indices):
        """
            Define the indexing operator [], to get array elements.
            Pass the indices as an indexible item

            The values in the tuple can be either absolute integer values e.g. (0,1,2...N) or
            relative indices as floats e.g. (0.5, 0.75), but must be consistent for the whole tuple.
        :param indices: a tuple of the indices to get
        :return: Array element term at index
        """
        if isinstance(indices[0],float): indices = self.convert_relative_indices_to_absolute_indices(indices)

        if self.num_of_dimensions == 1:
            return self.array[indices[0]]
        elif self.num_of_dimensions == 2:
            return self.array[indices[0],indices[1]]
        elif self.num_of_dimensions == 3:
            return self.array[indices[0], indices[1], indices[2]]
        return None

    def convert_relative_indices_to_absolute_indices(self, indices):
        assert len(indices) == self.num_of_dimensions, "Error: Number of indices must match number of dimensions"
        # un-offset and un-regularize
        new_indices = []
        for i in range(len(indices)):
            new_indices.append(int(indices[i] * self.offsets[i] + self.offsets[i]))
        return tuple(new_indices)

    def convert_absolute_indices_to_relative_indices(self, indices):
        assert len(indices) == self.num_of_dimensions, "Error: Number of indices must match number of dimensions"
        # offset then regularize
        new_indices = []
        for i in range(len(indices)):
            new_indices.append((indices[i] - self.offsets[i]) / self.offsets[i])
        return tuple(new_indices)

    def get_dimensions(self):
        return self.dimensions

def array_index_function(*coord_vars, self_obj=None,occurrence_time=None):
    """
        Populate a numpy array with the appropriate type of array element
    :param coord_vars:
    :param self_obj:
    :return:
    """
    absolute_indices = tuple([int(var) for var in coord_vars])

    if isinstance(self_obj, NALGrammar.Terms.StatementTerm):
        subject_is_array = isinstance(self_obj.get_subject_term(), NALGrammar.Terms.CompoundTerm) and isinstance(
            self_obj.get_subject_term().subterms[0], NALGrammar.Terms.ArrayTerm)
        predicate_is_array = isinstance(self_obj.get_predicate_term(),
                                        NALGrammar.Terms.CompoundTerm) and isinstance(
            self_obj.get_predicate_term().subterms[0], NALGrammar.Terms.ArrayTerm)
        if subject_is_array and predicate_is_array:
            subject_array_term = self_obj.get_subject_term().subterms[0]
            subject_atomic_element = subject_array_term[absolute_indices]  # get atomic array element
            predicate_array_term = self_obj.get_predicate_term().subterms[0]
            predicate_atomic_element = predicate_array_term[absolute_indices]  # get atomic array element
            element = NALGrammar.Terms.StatementTerm(
                subject_term=NALGrammar.Terms.CompoundTerm(subterms=[subject_atomic_element],
                                                           term_connector=NALSyntax.TermConnector.ExtensionalSetStart),
                predicate_term=NALGrammar.Terms.CompoundTerm(subterms=[predicate_atomic_element],
                                                             term_connector=NALSyntax.TermConnector.ExtensionalSetStart),
                copula=self_obj.get_copula())
        elif subject_is_array:
            array_term = self_obj.get_subject_term().subterms[0]
            atomic_element = array_term[absolute_indices]  # get atomic array element
            element = NALGrammar.Terms.StatementTerm(
                subject_term=NALGrammar.Terms.CompoundTerm(subterms=[atomic_element],
                                                           term_connector=NALSyntax.TermConnector.ExtensionalSetStart),
                predicate_term=self_obj.get_predicate_term(),
                copula=self_obj.get_copula())
        elif predicate_is_array:
            array_term = self_obj.get_predicate_term().subterms[0]
            atomic_element = array_term[absolute_indices]  # get atomic array element
            element = NALGrammar.Terms.StatementTerm(subject_term=self_obj.get_subject_term(),
                                                     predicate_term=NALGrammar.Terms.CompoundTerm(
                                                         subterms=[atomic_element],
                                                         term_connector=NALSyntax.TermConnector.ExtensionalSetStart),
                                                     copula=self_obj.get_copula())

    elif isinstance(self_obj, NALGrammar.Sentences.Judgment) or isinstance(self_obj, NALGrammar.Sentences.Goal):
        truth_value: NALGrammar.Values.TruthValue = self_obj.truth_values[absolute_indices]
        statement_element: NALGrammar.Terms.StatementTerm = self_obj.statement[
            absolute_indices]  # get atomic array element
        if isinstance(self_obj, NALGrammar.Sentences.Judgment):
            element = NALGrammar.Sentences.Judgment(statement=statement_element,
                                                    value=truth_value,
                                                    occurrence_time=occurrence_time)
        elif isinstance(self_obj, NALGrammar.Sentences.Goal):
            element = NALGrammar.Sentences.Goal(statement=statement_element,
                                                value=truth_value)

        if self_obj.image_array is not None:
            self_obj.image_array[absolute_indices] = (np.uint8)(
                truth_value.frequency * 255)  # Intensity
            self_obj.image_alpha_array[absolute_indices] = (np.uint8)(
                truth_value.confidence * 255)  # Alpha

        if self_obj.element_string_array is not None:
            self_obj.element_string_array[absolute_indices] = element.get_formatted_string()
        self_obj.stamp.evidential_base.merge_sentence_evidential_base_into_self(element)
    elif isinstance(self_obj, NALGrammar.Sentences.Question):
        statement_element: NALGrammar.Terms.StatementTerm = self_obj.statement[
            absolute_indices]  # get atomic array element
        element = NALGrammar.Sentences.Question(statement=statement_element)
        self_obj.stamp.evidential_base.merge_sentence_evidential_base_into_self(element)
    else:
        relative_indices = self_obj.convert_absolute_indices_to_relative_indices(absolute_indices)
        element = NALGrammar.Terms.ArrayTermElementTerm(array_term=self_obj, indices=relative_indices)

    return element