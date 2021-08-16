from NALGrammar.Arrays import Array
import Config
import Global
import NALSyntax
import Asserts

from NALGrammar.Terms import StatementTerm, CompoundTerm

from NALGrammar.Values import TruthValue, DesireValue
import NALInferenceRules
import numpy as np

import NARSGUI

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Enforces Narsese grammar that is used throughout the project
"""
class Sentence(Array):
    """
        sentence ::= <statement><punctuation> <tense> %<value>%
    """

    def __init__(self, statement, value, punctuation, occurrence_time=None):
        """

        :param statement:
        :param value: Pass as a tuple for array sentences (overall_truth, list_of_element_truth_values)
        :param punctuation:
        :param occurrence_time:
        :param array_truth_values:
        """
        Asserts.assert_punctuation(punctuation)
        assert isinstance(statement,StatementTerm) or isinstance(statement,CompoundTerm),"ERROR: Judgment needs a statement"
        self.statement = statement
        self.punctuation: NALSyntax.Punctuation = punctuation
        self.stamp = Stamp(self_sentence=self,occurrence_time=occurrence_time)

        if statement.is_array and hasattr(value, '__iter__') and value[1] is not None:
            if isinstance(self,Judgment) or isinstance(self,Goal):
                Array.__init__(self,statement.get_dimensions(),truth_values=value[1])
                self.value = value[0]
            else:
                Array.__init__(self, statement.get_dimensions())
                self.value = None
        else:
            #not an array
            Array.__init__(self, None)
            if hasattr(value, '__iter__'): # if its iterable, only use the primary truth-value
                value = value[0]
            self.value = value  # truth-value (for Judgment) or desire-value (for Goal) or None (for Question)

    def __str__(self):
        return self.get_formatted_string()

    def __hash__(self):
        """
            A Sentence is identified by its ID

            :return: Sentence ID
        """
        return self.stamp.id

    def is_event(self):
        return self.get_tense() != NALSyntax.Tense.Eternal

    def get_tense(self):
        return self.stamp.get_tense()

    def is_positive(self):
        """
            :returns: Is this statement True? (does it have more positive evidence than negative evidence?)
        """
        assert not isinstance(self,Question),"ERROR: Question cannot be positive."
        if self.is_event():
            time_projected_truth_value = self.get_value_projected_to_current_time()
            return NALInferenceRules.TruthValueFunctions.Expectation(time_projected_truth_value.frequency,
                                                                     time_projected_truth_value.confidence) >= Config.POSITIVE_THRESHOLD
        else:
            return NALInferenceRules.TruthValueFunctions.Expectation(self.value.frequency, self.value.confidence) >= Config.POSITIVE_THRESHOLD

    def is_negative(self):
        """
            :returns: Is this statement False? (does it have more negative evidence than positive evidence?)
        """
        assert not isinstance(self,Question),"ERROR: Question cannot be negative."
        if self.is_event():
            time_projected_truth_value = self.get_value_projected_to_current_time()
            return NALInferenceRules.TruthValueFunctions.Expectation(time_projected_truth_value.frequency,
                                                                     time_projected_truth_value.confidence) < Config.NEGATIVE_THRESHOLD
        else:
            return NALInferenceRules.TruthValueFunctions.Expectation(self.value.frequency, self.value.confidence) < Config.NEGATIVE_THRESHOLD

    def get_value_projected_to_current_time(self):
        """
            If this is an event, project its value to the current time
        """
        if self.is_event():
            return NALInferenceRules.TruthValueFunctions.F_Projection(self.value.frequency,
                                                           self.value.confidence,
                                                           self.stamp.occurrence_time,
                                                           Global.Global.get_current_cycle_number())
        else:
            return self.value

    def get_formatted_string(self):
        string = self.get_formatted_string_no_id()
        string = Global.Global.MARKER_SENTENCE_ID + str(self.stamp.id) + Global.Global.MARKER_ID_END + string
        return string

    def get_formatted_string_no_id(self):
        string = self.statement.get_formatted_string() + str(self.punctuation.value)
        if self.is_event(): string = string + " " + self.get_tense().value
        if self.value is not None: string = string + " " + self.get_value_projected_to_current_time().get_formatted_string()
        return string

    def mutually_add_to_interacted_sentences(self, other_sentence):
        self.stamp.interacted_sentences.append(other_sentence)
        if len(self.stamp.interacted_sentences) > Config.MAX_INTERACTED_SENTENCES_LENGTH:
            self.stamp.interacted_sentences.pop(0)

        other_sentence.stamp.interacted_sentences.append(self)
        if len(other_sentence.stamp.interacted_sentences) > Config.MAX_INTERACTED_SENTENCES_LENGTH:
            other_sentence.stamp.interacted_sentences.pop(0)

    def get_gui_info(self):
        dict = {}
        dict[NARSGUI.NARSGUI.KEY_STRING] = self.get_formatted_string()
        dict[NARSGUI.NARSGUI.KEY_TRUTH_VALUE] = str(self.value)
        dict[NARSGUI.NARSGUI.KEY_TIME_PROJECTED_TRUTH_VALUE] = None if self.stamp.occurrence_time is None else str(self.get_value_projected_to_current_time())
        dict[NARSGUI.NARSGUI.KEY_STRING_NOID] = self.get_formatted_string_no_id()
        dict[NARSGUI.NARSGUI.KEY_ID] = str(self.stamp.id)
        dict[NARSGUI.NARSGUI.KEY_OCCURRENCE_TIME] = self.stamp.occurrence_time
        dict[NARSGUI.NARSGUI.KEY_SENTENCE_TYPE] = type(self).__name__
        evidential_base_iterator = iter(self.stamp.evidential_base)
        next(
            evidential_base_iterator)  # skip the first element, which is just the sentence's ID so it' already displayed
        dict[NARSGUI.NARSGUI.KEY_LIST_EVIDENTIAL_BASE] = [str(evidence) for evidence in evidential_base_iterator]
        dict[NARSGUI.NARSGUI.KEY_LIST_INTERACTED_SENTENCES] = [str(interactedsentence) for interactedsentence in
                                           self.stamp.interacted_sentences]
        dict[NARSGUI.NARSGUI.KEY_IS_ARRAY] = self.is_array
        dict[NARSGUI.NARSGUI.KEY_ARRAY_IMAGE] = self.image_array if self.is_array and not isinstance(self,Question) else None
        dict[NARSGUI.NARSGUI.KEY_ARRAY_ALPHA_IMAGE] = self.image_alpha_array if self.is_array and not isinstance(self,Question) else None
        dict[NARSGUI.NARSGUI.KEY_ARRAY_ELEMENT_STRINGS] = self.element_string_array if self.is_array and not isinstance(self, Question) else None
        dict[NARSGUI.NARSGUI.KEY_DERIVED_BY] = self.stamp.derived_by
        dict[NARSGUI.NARSGUI.KEY_PARENT_PREMISES] = self.stamp.parent_premise_strings
        return dict


class Judgment(Sentence):
    """
        judgment ::= <statement>. %<truth-value>%
    """

    def __init__(self, statement, value,occurrence_time=None):
        Asserts.assert_valid_statement(statement)
        Sentence.__init__(self,
                          statement,
                          value,
                          NALSyntax.Punctuation.Judgment,
                          occurrence_time=occurrence_time)


class Question(Sentence):
    """
        question ::= <statement>? %<truth-value>%
    """

    def __init__(self, statement):
        Asserts.assert_valid_statement(statement)
        Sentence.__init__(self,
                          statement,
                          None,
                          NALSyntax.Punctuation.Question)


class Goal(Sentence):
    """
        goal ::= <statement>! %<desire-value>%
    """

    def __init__(self, statement, value):
        Asserts.assert_valid_statement(statement)
        Sentence.__init__(self,
                          statement,
                          value,
                          NALSyntax.Punctuation.Goal,
                          occurrence_time=Global.Global.get_current_cycle_number())

class Stamp:
    """
        Defines the metadata of a sentence, including
        when it was created, its occurrence time (when is its truth value valid),
        evidential base, etc.
    """
    def __init__(self, self_sentence, occurrence_time=None):
        self.id = Global.Global.NARS.memory.get_next_stamp_id()
        self.creation_time = Global.Global.get_current_cycle_number()  # when was this stamp created (in inference cycles)?
        self.occurrence_time = occurrence_time
        self.sentence = self_sentence
        self.evidential_base = EvidentialBase(self_sentence=self_sentence)
        self.interacted_sentences = []  # list of sentence this sentence has already interacted with
        self.derived_by = None
        self.parent_premise_strings = []
        self.from_one_premise_inference = False # is this sentence derived from one-premise inference?

    def get_tense(self):
        if self.occurrence_time is None:
            return NALSyntax.Tense.Eternal

        current_cycle = Global.Global.get_current_cycle_number()
        if self.occurrence_time < current_cycle:
            return NALSyntax.Tense.Past
        elif self.occurrence_time == current_cycle:
            return NALSyntax.Tense.Present
        elif self.occurrence_time > current_cycle:
            return NALSyntax.Tense.Future



class EvidentialBase:
    """
        Stores history of how the sentence was derived
    """
    def __init__(self,self_sentence):
        """
        :param id: Sentence ID
        """
        self.base = [self_sentence]  # array of sentences

    def __iter__(self):
        return iter(self.base)

    def __contains__(self, object):
        return object in self.base

    def merge_sentence_evidential_base_into_self(self, sentence):
        """
            Merge a Sentence's evidential base into self, including the Sentence itself.
            This function assumes the base to merge does not have evidential overlap with this base
            #todo figure out good way to store evidential bases such that older evidence is purged on overflow
        """
        for sentence in sentence.stamp.evidential_base:
            self.base.append(sentence)

        while len(self.base) > Config.MAX_EVIDENTIAL_BASE_LENGTH:
            self.base.pop(0)

    def has_evidential_overlap(self, other_base):
        """
            Check does other base has overlapping evidence with self?
            O(M + N)
            https://stackoverflow.com/questions/3170055/test-if-lists-share-any-items-in-python
        """
        return not set(self.base).isdisjoint(other_base.base)



def may_interact(j1,j2):
    """
        2 Sentences may interact if:
            # Neither is "None"
            # They are not the same Sentence
            # They have not previously interacted
            # One is not in the other's evidential base
            # They do not have overlapping evidential base
    :param j1:
    :param j2:
    :return: Are the sentence allowed to interact for inference
    """
    if j1 is None or j2 is None: return False
    if j1.stamp.id == j2.stamp.id: return False
    if j1 in j2.stamp.interacted_sentences or j2 in j1.stamp.interacted_sentences: return False
    if j1 in j2.stamp.evidential_base or j2 in j1.stamp.evidential_base: return False
    if j1.stamp.evidential_base.has_evidential_overlap(j2.stamp.evidential_base): return False
    return True

def new_sentence_from_string(sentence_string: str):
    """
        :param sentence_string - String of NAL syntax <term copula term>punctuation %frequency;confidence%

        :returns Sentence parsed from sentence_string
    """
    # Find statement start and statement end
    start_idx = sentence_string.find(NALSyntax.StatementSyntax.Start.value)
    assert (start_idx != -1), "Statement start character " + NALSyntax.StatementSyntax.Start.value + " not found."

    end_idx = sentence_string.rfind(NALSyntax.StatementSyntax.End.value)
    assert (end_idx != -1), "Statement end character " + NALSyntax.StatementSyntax.End.value + " not found."

    # Find sentence punctuation
    punctuation_idx = end_idx + 1
    assert (punctuation_idx < len(sentence_string)), "No punctuation found."
    punctuation_str = sentence_string[punctuation_idx]
    punctuation = NALSyntax.Punctuation.get_punctuation_from_string(punctuation_str)
    assert (punctuation is not None), punctuation_str + " is not punctuation."

    # Find Truth Value, if it exists
    start_truth_val_idx = sentence_string.find(NALSyntax.StatementSyntax.TruthValMarker.value, punctuation_idx)
    middle_truth_val_idx = sentence_string.find(NALSyntax.StatementSyntax.TruthValDivider.value, punctuation_idx)
    end_truth_val_idx = sentence_string.rfind(NALSyntax.StatementSyntax.TruthValMarker.value, punctuation_idx)

    truth_value_found = not (start_truth_val_idx == -1 or end_truth_val_idx == -1 or start_truth_val_idx == end_truth_val_idx)
    freq = None
    conf = None
    if truth_value_found:
        # Parse truth value from string
        freq = float(sentence_string[start_truth_val_idx + 1:middle_truth_val_idx])
        conf = float(sentence_string[middle_truth_val_idx + 1:end_truth_val_idx])

    # create the statement
    statement_string = sentence_string[start_idx:end_idx + 1]

    # create standard statement from string
    statement = StatementTerm.from_string(statement_string)

    if punctuation == NALSyntax.Punctuation.Judgment:
        if freq is None:
            # No truth value, use default truth value
            freq = Config.DEFAULT_JUDGMENT_FREQUENCY
            conf = Config.DEFAULT_JUDGMENT_CONFIDENCE
        truth_values = None
        if statement.is_array:
            def create_truth_value_array(*coord_vars):
                return TruthValue(freq, conf)

            func_vectorized = np.vectorize(create_truth_value_array)
            truth_values = np.fromfunction(function=func_vectorized, shape=statement.dim_lengths)

        sentence = Judgment(statement, (TruthValue(freq, conf),truth_values))
    elif punctuation == NALSyntax.Punctuation.Question:
        sentence = Question(statement)
    elif punctuation == NALSyntax.Punctuation.Goal:
        if freq is None:
            # No truth value, use default truth value
            freq = Config.DEFAULT_GOAL_FREQUENCY
            conf = Config.DEFAULT_GOAL_CONFIDENCE
        sentence = Goal(statement, DesireValue(freq,conf))
    else:
        assert False,"Error: No Punctuation!"

    # Find Tense, if it exists
    # otherwise mark it as eternal
    tense = NALSyntax.Tense.Eternal
    for t in NALSyntax.Tense:
        if t != NALSyntax.Tense.Eternal:
            tense_idx = sentence_string.find(t.value)
            if tense_idx != -1:  # found a tense
                tense = NALSyntax.Tense.get_tense_from_string(sentence_string[tense_idx: tense_idx + len(t.value)])
                break

    if tense == NALSyntax.Tense.Present:
        #Mark present tense event as happening right now!
        sentence.stamp.occurrence_time = Global.Global.get_current_cycle_number()

    return sentence