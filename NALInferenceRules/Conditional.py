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
import Asserts
import NALGrammar
import NALSyntax
from NALInferenceRules import TruthValueFunctions, HelperFunctions


def ConditionalAnalogy(j1, j2):
    """
        Conditional Analogy

        Input:
            j1: Statement (S) <f1, c1> {tense}

            j2: Equivalence Statement (S <=> P)  <f2, c2>
        Evidence:
            F_analogy
        Returns:
            :- Sentence (P <f3, c3>)
    """
    Asserts.assert_sentence_equivalence(j2)
    Asserts.assert_sentence(j2)

    # Statement
    if j1.statement == j2.statement.get_subject_term():
        result_statement: NALGrammar.Terms.StatementTerm = j2.statement.get_predicate_term()
    elif j1.statement == j2.statement.get_predicate_term():
        result_statement: NALGrammar.Terms.StatementTerm = j2.statement.get_subject_term()
    else:
        assert False, "Error: Invalid inputs to Conditional Analogy: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    return HelperFunctions.create_resultant_sentence_two_premise(j1,
                                                                 j2,
                                                                 result_statement,
                                                                 TruthValueFunctions.F_Analogy)



def ConditionalDeduction(j1, j2):
    """
        Conditional Deduction

        Input:
            j1: Implication Statement (S ==> P) <f2, c2>

            j2: Statement (S) <f1, c1> {tense}
        Evidence:
            F_deduction
        Returns:
            :- P <f3, c3>
    """
    Asserts.assert_sentence_forward_implication(j1)
    assert j2.statement == j1.statement.get_subject_term(), "Error: Invalid inputs to Conditional Deduction: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()
    result_statement: NALGrammar.Terms.StatementTerm = j1.statement.get_predicate_term() # P

    return HelperFunctions.create_resultant_sentence_two_premise(j1,
                                                                 j2,
                                                                 result_statement,
                                                                 TruthValueFunctions.F_Deduction)


def ConditionalAbduction(j1, j2):
    """
        Conditional Abduction

        Input:
            j1: Implication Statement (S ==> P) <f2, c2>

            j2: Event (P) <f1, c1> {tense}
        Evidence:
            F_abduction
        Returns:
            :- S <f3, c3>
    """
    Asserts.assert_sentence_forward_implication(j1)
    assert j2.statement == j1.statement.get_predicate_term(), "Error: Invalid inputs to Conditional Abduction: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    result_statement: NALGrammar.Terms.StatementTerm = j1.statement.get_subject_term() # S

    return HelperFunctions.create_resultant_sentence_two_premise(j1,
                                                                 j2,
                                                                 result_statement,
                                                                 TruthValueFunctions.F_Abduction)


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

            j2: Statement (S) <f1, c1> {tense}
        Evidence:
            F_deduction
        Returns:
            :-  ((C1 && C2 && ... CN) ==> P)  <f3, c3>
    """
    Asserts.assert_sentence_forward_implication(j1)

    subject_term: NALGrammar.Terms.CompoundTerm = j1.statement.get_subject_term()

    new_subterms = list(set(subject_term.subterms) - {j2.statement}) # subtract j2 from j1 subject subterms

    if len(new_subterms) > 1:
        # recreate the conjunctional compound with the new subterms
        new_compound_subject_term = NALGrammar.Terms.CompoundTerm(new_subterms, subject_term.connector)
    elif len(new_subterms) == 1:
        # only 1 subterm, no need to make it a compound
        new_compound_subject_term = new_subterms[0]
    else:
        # 0 new subterms
        if len(subject_term.subterms) > 1:
            new_subterms = subject_term.subterms.copy()
            new_subterms.pop()
            new_compound_subject_term = NALGrammar.Terms.CompoundTerm(new_subterms, subject_term.connector)
        else:
            assert False,"ERROR: Invalid inputs to Conditional Conjunctional Deduction " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    result_statement = NALGrammar.Terms.StatementTerm(new_compound_subject_term, j1.statement.get_predicate_term(),
                                                      j1.statement.get_copula())

    return HelperFunctions.create_resultant_sentence_two_premise(j1,
                                                                 j2,
                                                                 result_statement,
                                                                 TruthValueFunctions.F_Deduction)

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

        #todo temporal
    """

    Asserts.assert_sentence_forward_implication(j1)
    Asserts.assert_sentence_forward_implication(j2)

    j1_subject_term = j1.statement.get_subject_term()
    j2_subject_term = j2.statement.get_subject_term()

    j1_subject_statement_terms = j1_subject_term.subterms if NALSyntax.TermConnector.is_conjunction(
        j1_subject_term.connector) else [j1_subject_term]

    j2_subject_statement_terms = j2_subject_term.subterms if NALSyntax.TermConnector.is_conjunction(
        j2_subject_term.connector) else [j2_subject_term]

    set_difference_of_terms = list(set(j1_subject_statement_terms) - set(j2_subject_statement_terms))

    if len(set_difference_of_terms) != 1: assert False, "Error, should only have one term in set difference: " + str([term.get_formatted_string() for term in set_difference_of_terms])

    result_statement: NALGrammar.Terms.StatementTerm = set_difference_of_terms[0]


    return HelperFunctions.create_resultant_sentence_two_premise(j1,
                                                                 j2,
                                                                 result_statement,
                                                                 TruthValueFunctions.F_Abduction)