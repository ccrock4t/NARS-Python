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


def ConditionalAnalogy(j1, j2):
    """
        Conditional Analogy

        Input:
            j1: Statement (S) <f2, c2>

            j2: Equivalence Statement (S <=> P)  <f1, c1> {tense}
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

    if isinstance(j2, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Analogy(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j2.stamp.occurrence_time)
    elif isinstance(j2, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def ConditionalDeduction(j1, j2):
    """
        Conditional Deduction

        Input:
            j1: Equivalence Statement (S ==> P) <f2, c2>

            j2: Statement (S) <f1, c1> {tense}
        Evidence:
            F_deduction
        Returns:
            :- P <f3, c3>
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    statement_term: NALGrammar.StatementTerm = j1.statement.get_predicate_term() # P
    result_statement = NALGrammar.Statement(statement_term.get_subject_term(), statement_term.get_predicate_term(),
                                            statement_term.get_copula())


    if isinstance(j2, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Deduction(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j2.stamp.occurrence_time)
    elif isinstance(j2, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def ConditionalAbduction(j1, j2):
    """
        Conditional Abduction

        Input:
            j1: Equivalence Statement (S ==> P) <f2, c2>

            j2: Event (P) <f1, c1> {tense}
        Evidence:
            F_deduction
        Returns:
            :- P <f3, c3>
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    statement_term: NALGrammar.StatementTerm = j1.statement.get_subject_term() # S
    result_statement = NALGrammar.Statement(statement_term.get_subject_term(), statement_term.get_predicate_term(),
                                            statement_term.get_copula())


    if isinstance(j2, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Abduction(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j2, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def ConditionalInduction(j1, j2):
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


def ConditionalComparison(j1, j2):
    """
        Temporal Comparison

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

"""
    Conditional Conjunctional Rules
    --------------------------------
    Conditional Rules w/ Conjunctions
"""
def ConditionalConjunctionalDeduction(j1, j2):
    """
        Conditional Conjunctional Deduction

        Input:
            j1: Implication Statement ((C1 && C2 && ... CN && S) ==> P) <f2, c2>

            j2: Implication Statement (S) <f1, c1> {tense}
        Evidence:
            F_deduction
        Returns:
            :-  ((C1 && C2 && ... CN) ==> P)  <f3, c3>
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    subject_term: NALGrammar.CompoundTerm = j1.statement.get_subject_term()

    new_subterms = list(set(subject_term.subterms) - {j2.statement.term})

    if len(new_subterms) > 1:
        new_compound_subject_term = NALGrammar.CompoundTerm(new_subterms, subject_term.connector)
    else:
        new_compound_subject_term = new_subterms[0]

    result_statement = NALGrammar.Statement(new_compound_subject_term, j1.statement.get_predicate_term(),
                                            j1.statement.get_copula())


    if isinstance(j2, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Deduction(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j2.stamp.occurrence_time)
    elif isinstance(j2, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def ConditionalConjunctionalAbduction(j1, j2):
    """
        Conditional Conjunctional Abduction

        Input:
            j1: Implication Statement ((C1 && C2 && ... CN && S) ==> P) <f1, c1>

            j2: Implication Statement ((C1 && C2 && ... CN) ==> P) <f2, c2> {tense}
        Evidence:
            F_abduction
        Returns:
            :-  S  <f3, c3>
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    j1_subject_term = j1.statement.get_subject_term()
    j2_subject_term = j2.statement.get_subject_term()

    j1_subject_statement_terms = j1_subject_term.subterms if NALSyntax.TermConnector.is_conjunction(
        j1_subject_term.connector) else [j1_subject_term]

    j2_subject_statement_terms = j2_subject_term.subterms if NALSyntax.TermConnector.is_conjunction(
        j2_subject_term.connector) else [j2_subject_term]

    set_difference_of_terms = list(set(j1_subject_statement_terms) - set(j2_subject_statement_terms))

    if len(set_difference_of_terms) != 1: assert False, "Error, should only have one term in set difference: " + str([term.get_formatted_string() for term in set_difference_of_terms])

    result_term: NALGrammar.StatementTerm = set_difference_of_terms[0]
    result_statement = NALGrammar.Statement(result_term.get_subject_term(), result_term.get_predicate_term(),
                                            result_term.get_copula())

    if isinstance(j2, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Abduction(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j2.stamp.occurrence_time)
    elif isinstance(j2, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result