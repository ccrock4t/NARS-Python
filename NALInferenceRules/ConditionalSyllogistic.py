"""
==== ==== ==== ==== ==== ====
==== NAL Inference Rules - Conditional Syllogistic Inference Rules ====
==== ==== ==== ==== ==== ====

    Author: Christian Hahm
    Created: October 8, 2020
    Purpose: Defines the NAL inference rules
            Assumes the given sentences do not have evidential overlap.
            Does combine evidential bases in the Resultant Sentence.
"""
import NALGrammar
import NALSyntax
from NALInferenceRules import TruthValueFunctions
from NALInferenceRules.HelperFunctions import getevidentialvalues_from2sentences


def Analogy(j1, j2):
    """
        Conditional Analogy

        Input:
            j1: Event (S) <f1, c1> {tense}

            j2: Equivalence Statement (S <=> P) <f2, c2>
        Evidence:
            F_analogy
        Returns:
            :- Sentence (P <f3, c3>)
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    if j1.statement.term == j2.statement.get_subject_term():
        statement_term: NALGrammar.StatementTerm = j2.statement.get_predicate_term()
    elif j1.statement.term == j2.statement.get_predicate_term():
        statement_term: NALGrammar.StatementTerm  = j2.statement.get_subject_term()
    else:
        assert False, "Error: Invalid inputs to Conditional Analogy: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    result_statement = NALGrammar.Statement(statement_term.get_subject_term(), statement_term.get_predicate_term(),
                                            statement_term.get_copula())


    if isinstance(j1, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Analogy(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def Deduction(j1, j2):
    """
        Conditional Deduction

        Input:
            j1: Event (S) <f1, c1> {tense}

            j2: Equivalence Statement (S ==> P) <f2, c2>
        Evidence:
            F_deduction
        Returns:
            :- P <f3, c3>
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    statement_term: NALGrammar.StatementTerm = j2.statement.get_predicate_term() # P
    result_statement = NALGrammar.Statement(statement_term.get_subject_term(), statement_term.get_predicate_term(),
                                            statement_term.get_copula())


    if isinstance(j1, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Deduction(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def Abduction(j1, j2):
    """
        Conditional Abduction

        Input:
            j1: Event (P) <f1, c1> {tense}

            j2: Equivalence Statement (S ==> P) <f2, c2>
        Evidence:
            F_deduction
        Returns:
            :- P <f3, c3>
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    statement_term: NALGrammar.StatementTerm = j2.statement.get_subject_term() # S
    result_statement = NALGrammar.Statement(statement_term.get_subject_term(), statement_term.get_predicate_term(),
                                            statement_term.get_copula())


    if isinstance(j1, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Abduction(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def Induction(j1, j2):
    """
        Temporal Induction

        Input:
            j1: Event S <f1, c1> {tense}

            j2: Event P <f2, c2> {tense}
        Evidence:
            w+: and(f1,f2,c1,c2)

            w-: and(f2,c2,not(f1),c1)

            w: and(f2,c1,c2)
        Returns:
            :- Sentence (S =|> P <f3, c3>)
            :- or Sentence (S =/> P <f3, c3>)
            :- or Sentence (P =/> S <f3, c3>)
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
    (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
    j1_statement_term = j1.statement.term
    j2_statement_term = j2.statement.term

    if j1.stamp.occurrence_time == j2.stamp.occurrence_time:
        # j1 =|> j2
        result_statement = NALGrammar.Statement(j1_statement_term, j2_statement_term,
                                                NALSyntax.Copula.ConcurrentImplication)
    elif j1.stamp.occurrence_time < j2.stamp.occurrence_time:
        # j1 =/> j2
        result_statement = NALGrammar.Statement(j1_statement_term, j2_statement_term,
                                                NALSyntax.Copula.PredictiveImplication)
    elif j2.stamp.occurrence_time < j1.stamp.occurrence_time:
        # j2 =/> j1
        result_statement = NALGrammar.Statement(j2_statement_term, j1_statement_term,
                                                NALSyntax.Copula.PredictiveImplication)

    # calculate induction truth value
    result_truth = TruthValueFunctions.F_Induction(f1, c1, f2, c2)
    result = NALGrammar.Judgment(result_statement, result_truth)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def Comparison(j1, j2):
    """
        Temporal Induction

        Input:
            A: Event S <f1, c1> {tense}

            B: Event P <f2, c2> {tense}
        Evidence:
            w+: and(f1,f2,c1,c2)

            w-: and(f2,c2,not(f1),c1)

            w: and(f2,c1,c2)
        Returns:
            :- Sentence (S <|> P <f3, c3>)
            :- or Sentence (S </> P <f3, c3>)
            :- or Sentence (P </> S <f3, c3>)
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
    (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
    j1_statement_term = j1.statement.term
    j2_statement_term = j2.statement.term

    if j1.stamp.occurrence_time == j2.stamp.occurrence_time:
        # <|>
        result_statement = NALGrammar.Statement(j1_statement_term, j2_statement_term,
                                                NALSyntax.Copula.ConcurrentEquivalence)
    elif j1.stamp.occurrence_time < j2.stamp.occurrence_time:
        # j1 </> j2
        result_statement = NALGrammar.Statement(j1_statement_term, j2_statement_term,
                                                NALSyntax.Copula.PredictiveEquivalence)
    elif j2.stamp.occurrence_time < j1.stamp.occurrence_time:
        # j2 </> j1
        result_statement = NALGrammar.Statement(j2_statement_term, j1_statement_term,
                                                NALSyntax.Copula.PredictiveEquivalence)

    # calculate induction truth value
    result_truth = TruthValueFunctions.F_Comparison(f1, c1, f2, c2)
    result = NALGrammar.Judgment(result_statement, result_truth)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result
