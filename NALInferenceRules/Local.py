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
import Config
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
    NALGrammar.Asserts.assert_sentence(j1)
    NALGrammar.Asserts.assert_sentence(j2)
    assert (
            j1.statement.get_formatted_string() == j2.statement.get_formatted_string()), "Cannot revise sentences for 2 different statements"

    # todo handle occurrence_time
    occurrence_time = None

    # Get Truth Value
    (wp1, w1, wn1), (wp2, w2, wn2) = HelperFunctions.getevidence_from2sentences(j1, j2)
    result_truth = TruthValueFunctions.F_Revision(wp1=wp1, wn1=wn1, wp2=wp2, wn2=wn2)

    result_statement = NALGrammar.Terms.StatementTerm(j1.statement.get_subject_term(),
                                                      j1.statement.get_predicate_term(),
                                                      j1.statement.get_copula())
    result = NALGrammar.Sentences.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


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
    NALGrammar.Asserts.assert_sentence(j1)
    NALGrammar.Asserts.assert_sentence(j2)
    # Subject Predicate
    subjpred1 = j1.subject_predicate
    subjpred2 = j2.subject_predicate

    # Truth Value
    (f1, c1), (f2, c2) = HelperFunctions.getevidentialvalues_from2sentences(j1, j2)

    # Make the choice
    if subjpred1 == subjpred2:
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


def Decision(f, c):
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
    desirability = TruthValueFunctions.Expectation(f, c)
    return abs(desirability - 0.5) > Config.T

def Eternalization(j):
    """
        Eternalization
        :param j:
        :return: Eternalized form of j
    """
    NALGrammar.Asserts.assert_sentence(j)

    if isinstance(j, NALGrammar.Sentences.Judgment):
        result_truth = TruthValueFunctions.F_Eternalization(j.value.frequency, j.value.confidence)
        result = NALGrammar.Sentences.Judgment(j.statement, result_truth, occurrence_time=None)
    elif isinstance(j, NALGrammar.Sentences.Question):
        assert "error"

    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)

    return result

def Projection(j, occurrence_time):
    """
        Projection
        :param j:
        :param occurrence_time: occurrence time to project j to
        :return: Projected form of j
    """
    NALGrammar.Asserts.assert_sentence(j)

    if isinstance(j, NALGrammar.Sentences.Judgment):
        result_truth = TruthValueFunctions.F_Projection(j.value.frequency, j.value.confidence, j.stamp.occurrence_time, occurrence_time)
        result = NALGrammar.Sentences.Judgment(j.statement, result_truth, occurrence_time=occurrence_time)
    elif isinstance(j, NALGrammar.Sentences.Question):
        assert "error"

    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)

    return result