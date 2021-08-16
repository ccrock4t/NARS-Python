"""
==== ==== ==== ==== ==== ====
==== NAL Inference Rules - Local Inference Rules ====
==== ==== ==== ==== ==== ====

    Author: Christian Hahm
    Created: October 8, 2020
    Purpose: Defines the NAL inference rules
            Assumes the given sentences do not have evidential overlap.
            Does combine evidential bases in the Resultant Sentence.
"""
import Asserts
import Config
import Global
import NALGrammar
from NALInferenceRules import HelperFunctions, TruthValueFunctions


def Revision(j1, j2):
    """
        Revision Rule

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Revises two instances of the same sentence with different truth values.

        Input:
          j1: Sentence (Statement <f1, c1>)

          j2: Sentence (Statement <f2, c2>)
        Returns:
          :- Sentence (Statement <f3, c3>)
    """
    Asserts.assert_sentence(j1)
    Asserts.assert_sentence(j2)
    assert (
            j1.statement.get_formatted_string() == j2.statement.get_formatted_string()), "Cannot revise sentences for 2 different statements"

    result_statement = NALGrammar.Terms.StatementTerm(j1.statement.get_subject_term(),
                                                      j1.statement.get_predicate_term(),
                                                      j1.statement.get_copula())

    return HelperFunctions.create_resultant_sentence_two_premise(j1,
                                                                 j2,
                                                                 result_statement,
                                                                 TruthValueFunctions.F_Revision)


def Choice(j1, j2):
    """
         Choice Rule

         -----------------

         Choose the better answer (according to the choice rule) between 2 different sentences.
         If the statements are the same, the statement with the highest confidence is chosen.
         If they are different, the statement with the highest expectation is chosen.

         Input:
           j1: Sentence (Statement <f1, c1>)

           j2: Sentence (Statement <f2, c2>)

         Returns:
           j1 or j2, depending on which is better according to the choice rule
    """
    Asserts.assert_sentence(j1)
    Asserts.assert_sentence(j2)

    # Truth Value
    (f1, c1), (f2, c2) = HelperFunctions.getevidentialvalues_from2sentences(j1, j2)

    # Make the choice
    if j1.statement == j2.statement:
        if c1 >= c2:
            best = j1
        else:
            best = j2
    else:
        e1 = TruthValueFunctions.Expectation(f1, c1)
        e2 = TruthValueFunctions.Expectation(f2, c2)
        if e1 >= e2:
            best = j1
        else:
            best = j2

    return best


def Decision(j):
    """
         Decision Rule

         -----------------

         Make the decision to purse a desire based on its expected desirability

         Input:
           f: Desire-value frequency
           c: Desire-value confidence

         Returns:
           True or false, whether to pursue the goal
    """
    value = j.get_value_projected_to_current_time()
    desirability = TruthValueFunctions.Expectation(value.frequency, value.confidence)
    return desirability > Config.T

def Eternalization(j):
    """
        Eternalization
        :param j:
        :return: Eternalized form of j
    """
    Asserts.assert_sentence(j)

    if isinstance(j, NALGrammar.Sentences.Judgment):
        result_truth = TruthValueFunctions.F_Eternalization(j.value.frequency, j.value.confidence)
        result = NALGrammar.Sentences.Judgment(j.statement, result_truth, occurrence_time=None)
    elif isinstance(j, NALGrammar.Sentences.Question):
        assert "error"

    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)

    return result

def Projection(j, occurrence_time):
    """
        Projection.

        Returns j projected to the given occurrence time.

        :param j:
        :param occurrence_time: occurrence time to project j to
        :return: Projected form of j
    """
    Asserts.assert_sentence(j)

    if isinstance(j, NALGrammar.Sentences.Judgment):
        result_truth = TruthValueFunctions.F_Projection(j.value.frequency, j.value.confidence, j.stamp.occurrence_time, occurrence_time)
        result = NALGrammar.Sentences.Judgment(j.statement, result_truth, occurrence_time=occurrence_time)
    elif isinstance(j, NALGrammar.Sentences.Question):
        assert "error"

    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)

    return result