"""
==== ==== ==== ==== ==== ====
==== NAL Inference Rules - Syllogistic Inference Rules ====
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


def Deduction(j1, j2):
    """
        Deduction (Strong syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M --> P <f1, c1>)

            j2: Sentence (S --> M <f2, c2>)
        Truth Val:
            F_ded
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    Asserts.assert_sentence_asymmetric(j1)
    Asserts.assert_sentence_asymmetric(j2)

    # Statement
    result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_subject_term(),
                                                      j1.statement.get_predicate_term(),
                                                      j1.statement.get_copula())

    return HelperFunctions.create_resultant_sentence_two_premise(j1, j2, result_statement, TruthValueFunctions.F_Deduction)


def Analogy(j1, j2):
    """
        Analogy (Strong syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M --> P <f1, c1>)
                or
            j1: Sentence (P --> M <f1, c1>)

            j2: Sentence (S <-> M <f2, c2>)
        Truth Val:
            F_ana
        Returns: (depending on j1)
            :- Sentence (S --> P <f3, c3>)
                or
            :- Sentence (P --> S <f3, c3>)

    """
    Asserts.assert_sentence_asymmetric(j1)
    Asserts.assert_sentence_symmetric(j2)

    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_predicate_term():
        # j1=M-->P, j2=S<->M
        result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_subject_term(),
                                                          j1.statement.get_predicate_term(),
                                                          j1.statement.get_copula())  # S-->P
    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1=M-->P, j2=M<->S
        result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_predicate_term(),
                                                          j1.statement.get_predicate_term(),
                                                          j1.statement.get_copula())  # S-->P
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1=P-->M, j2=S<->M
        result_statement = NALGrammar.Terms.StatementTerm(j1.statement.get_subject_term(),
                                                          j2.statement.get_subject_term(),
                                                          j1.statement.get_copula())  # P-->S
    elif j1.statement.get_predicate_term() == j2.statement.get_subject_term():
        # j1=P-->M, j2=M<->S
        result_statement = NALGrammar.Terms.StatementTerm(j1.statement.get_subject_term(),
                                                          j2.statement.get_predicate_term(),
                                                          j1.statement.get_copula())  # P-->S
    else:
        assert (
            False), "Error: Invalid inputs to nal_analogy: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    return HelperFunctions.create_resultant_sentence_two_premise(j1, j2, result_statement, TruthValueFunctions.F_Analogy)



def Resemblance(j1, j2):
    """
        Resemblance (Strong syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M <-> P <f1, c1>)
                or
            j1: Sentence (P <-> M <f1, c1>)

            j2: Sentence (S <-> M <f2, c2>)
                or
            j2: Sentence (M <-> S <f2, c2>)
        Truth Val:
            F_res
        Returns:
            :- Sentence (S <-> P <f3, c3>)
    """
    Asserts.assert_sentence_symmetric(j1)
    Asserts.assert_sentence_symmetric(j2)

    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_predicate_term():
        # j1=M<->P, j2=S<->M
        result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_subject_term(),
                                                          j1.statement.get_predicate_term(),
                                                          j1.statement.get_copula())  # S<->P
    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1=M<->P, j2=M<->S
        result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_predicate_term(),
                                                          j1.statement.get_predicate_term(),
                                                          j1.statement.get_copula())  # S<->P
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1=P<->M, j2=S<->M
        result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_subject_term(),
                                                          j1.statement.get_subject_term(),
                                                          j1.statement.get_copula())  # S<->P
    elif j1.statement.get_predicate_term() == j2.statement.get_subject_term():
        # j1=P<->M, j2=M<->S
        result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_predicate_term(),
                                                          j2.statement.get_subject_term(),
                                                          j1.statement.get_copula())  # S<->P
    else:
        assert (
            False), "Error: Invalid inputs to nal_resemblance: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    return HelperFunctions.create_resultant_sentence_two_premise(j1, j2, result_statement, TruthValueFunctions.F_Resemblance)


def Abduction(j1, j2):
    """
        Abduction (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (P --> M <f1, c1>)

            j2: Sentence (S --> M <f2, c2>)
        Evidence:
            F_abd
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    Asserts.assert_sentence_asymmetric(j1)
    Asserts.assert_sentence_asymmetric(j2)

    # Statement
    result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_subject_term(),
                                                      j1.statement.get_subject_term(),
                                                      j1.statement.get_copula())

    return HelperFunctions.create_resultant_sentence_two_premise(j1, j2, result_statement, TruthValueFunctions.F_Abduction)


def Induction(j1, j2):
    """
        Induction (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M --> P <f1, c1>)

            j2: Sentence (M --> S <f2, c2>)
        Evidence:
            F_ind
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    Asserts.assert_sentence_asymmetric(j1)
    Asserts.assert_sentence_asymmetric(j2)

    # Statement
    result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_predicate_term(),
                                                      j1.statement.get_predicate_term(), j1.statement.get_copula())
    return HelperFunctions.create_resultant_sentence_two_premise(j1, j2, result_statement, TruthValueFunctions.F_Induction)


def Exemplification(j1, j2):
    """
        Exemplification (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (P --> M <f1, c1>)

            j2: Sentence (M --> S <f2, c2>)
        Evidence:
            F_exe
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    Asserts.assert_sentence_asymmetric(j1)
    Asserts.assert_sentence_asymmetric(j2)

    # Statement
    result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_predicate_term(),
                                                      j1.statement.get_subject_term(), j1.statement.get_copula())
    return HelperFunctions.create_resultant_sentence_two_premise(j1, j2, result_statement, TruthValueFunctions.F_Exemplification)


def Comparison(j1, j2):
    """
        Comparison (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M --> P <f1, c1>)
            j2: Sentence (M --> S <f2, c2>)

            or

            j1: Sentence (P --> M <f1, c1>)
            j2: Sentence (S --> M <f2, c2>)
        Evidence:
            F_com
        Returns:
            :- Sentence (S <-> P <f3, c3>)
    """
    Asserts.assert_sentence_asymmetric(j1)
    Asserts.assert_sentence_asymmetric(j2)

    copula = NALSyntax.Copula.Similarity if NALSyntax.Copula.is_first_order(j1.statement.get_copula()) else NALSyntax.Copula.Equivalence
    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # M --> P and M --> S

        result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_predicate_term(),
                                                          j1.statement.get_predicate_term(),
                                                          copula)
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # P --> M and S --> M
        result_statement = NALGrammar.Terms.StatementTerm(j2.statement.get_subject_term(),
                                                          j1.statement.get_subject_term(),
                                                          copula)
    else:
        assert (
            False), "Error: Invalid inputs to nal_comparison: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    if j1.is_array and j2.is_array:
        truth_function = TruthValueFunctions.F_Array_Element_Comparison
    else:
        truth_function = TruthValueFunctions.F_Comparison

    return HelperFunctions.create_resultant_sentence_two_premise(j1,j2,result_statement,truth_function)