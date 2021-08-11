import NALGrammar
import NALSyntax
from NALInferenceRules import TruthValueFunctions, HelperFunctions
"""
==== ==== ==== ==== ==== ====
==== NAL Inference Rules - Truth Value Functions ====
==== ==== ==== ==== ==== ====

    Author: Christian Hahm
    Created: August 11, 2021
    Purpose: Defines the NAL temporal inference rules
            Assumes the given sentences do not have evidential overlap.
            Does combine evidential bases in the Resultant Sentence.
"""
def TemporalInduction(j1, j2):
    """
        Temporal Induction

        Input:
            j1: Event S <f1, c1> {tense}

            j2: Event P <f2, c2> {tense}
        Evidence:
            F_induction
        Returns:
            :- Sentence (S =|> P <f3, c3>)
            :- or Sentence (S =/> P <f3, c3>)
            :- or Sentence (P =/> S <f3, c3>)
    """
    assert j1.stamp.get_tense() != NALSyntax.Tense.Eternal and j2.stamp.get_tense() != NALSyntax.Tense.Eternal,"ERROR: Temporal Induction needs events"

    j1_statement_term = j1.statement
    j2_statement_term = j2.statement

    if j1.stamp.occurrence_time == j2.stamp.occurrence_time:
        # j1 =|> j2
        result_statement = NALGrammar.Terms.StatementTerm(j1_statement_term, j2_statement_term,
                                                          NALSyntax.Copula.ConcurrentImplication)
    elif j1.stamp.occurrence_time < j2.stamp.occurrence_time:
        # j1 =/> j2
        result_statement = NALGrammar.Terms.StatementTerm(j1_statement_term, j2_statement_term,
                                                          NALSyntax.Copula.PredictiveImplication)
    elif j2.stamp.occurrence_time < j1.stamp.occurrence_time:
        # j2 =/> j1
        result_statement = NALGrammar.Terms.StatementTerm(j2_statement_term, j1_statement_term,
                                                          NALSyntax.Copula.PredictiveImplication)

    return HelperFunctions.create_resultant_sentence_two_premise(j1, j2, result_statement,
                                                                 TruthValueFunctions.F_Induction)


def TemporalComparison(j1, j2):
    """
        Temporal Comparison

        Input:
            A: Event S <f1, c1> {tense}

            B: Event P <f2, c2> {tense}
        Evidence:
            F_comparison
        Returns:
            :- Sentence (S <|> P <f3, c3>)
            :- or Sentence (S </> P <f3, c3>)
            :- or Sentence (P </> S <f3, c3>)
    """
    assert j1.stamp.get_tense() != NALSyntax.Tense.Eternal and j2.stamp.get_tense() != NALSyntax.Tense.Eternal, "ERROR: Temporal Comparison needs events"

    j1_statement_term = j1.statement
    j2_statement_term = j2.statement

    if j1.stamp.occurrence_time == j2.stamp.occurrence_time:
        # <|>
        result_statement = NALGrammar.Terms.StatementTerm(j1_statement_term, j2_statement_term,
                                                          NALSyntax.Copula.ConcurrentEquivalence)
    elif j1.stamp.occurrence_time < j2.stamp.occurrence_time:
        # j1 </> j2
        result_statement = NALGrammar.Terms.StatementTerm(j1_statement_term, j2_statement_term,
                                                          NALSyntax.Copula.PredictiveEquivalence)
    elif j2.stamp.occurrence_time < j1.stamp.occurrence_time:
        # j2 </> j1
        result_statement = NALGrammar.Terms.StatementTerm(j2_statement_term, j1_statement_term,
                                                          NALSyntax.Copula.PredictiveEquivalence)

    return HelperFunctions.create_resultant_sentence_two_premise(j1, j2, result_statement, TruthValueFunctions.F_Comparison)

def TemporalIntersection(j1, j2):
    """
        Temporal Intersection

        Input:
            j1: Event S <f1, c1> {tense}

            j2: Event P <f2, c2> {tense}
        Evidence:
            F_Intersection
        Returns:
            :- Event (S &/ P <f3, c3>)
            :- or Event (P &/ S <f3, c3>)
            :- or Event (S &| P <f3, c3>)
    """
    assert j1.stamp.get_tense() != NALSyntax.Tense.Eternal and j2.stamp.get_tense() != NALSyntax.Tense.Eternal,"ERROR: Temporal Induction needs events"

    j1_statement_term = j1.statement
    j2_statement_term = j2.statement

    result = None
    if j1.stamp.occurrence_time == j2.stamp.occurrence_time:
        # j1 &| j2
        result_statement = NALGrammar.Terms.CompoundTerm([j1_statement_term, j2_statement_term],
                                                          NALSyntax.TermConnector.ParallelConjunction)
        result = HelperFunctions.create_resultant_sentence_two_premise(j1, j2, result_statement,
                                                              TruthValueFunctions.F_Intersection)
    elif j1.stamp.occurrence_time < j2.stamp.occurrence_time:
        # j1 &/ j2
        result_statement = NALGrammar.Terms.CompoundTerm([j1_statement_term, j2_statement_term],
                                                          NALSyntax.TermConnector.SequentialConjunction)
        result = HelperFunctions.create_resultant_sentence_two_premise(j1, j2, result_statement,
                                                              TruthValueFunctions.F_Intersection)
    elif j2.stamp.occurrence_time < j1.stamp.occurrence_time:
        # j2 &/ j1
        result_statement = NALGrammar.Terms.CompoundTerm([j2_statement_term, j1_statement_term],
                                                          NALSyntax.TermConnector.SequentialConjunction)
        result = HelperFunctions.create_resultant_sentence_two_premise(j2, j1, result_statement,
                                                              TruthValueFunctions.F_Intersection)

    return result