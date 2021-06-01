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
import NALGrammar
import NALSyntax
from NALInferenceRules import TruthValueFunctions
from NALInferenceRules.HelperFunctions import getevidentialvalues_from2sentences


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
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    result_statement = NALGrammar.StatementTerm(j2.statement.get_subject_term(),
                                            j1.statement.get_predicate_term(),
                                            j1.statement.get_copula())

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
            f: and(f1,f2)

            c: and(f2,c1,c2)
        Returns: (depending on j1)
            :- Sentence (S --> P <f3, c3>)
                or
            :- Sentence (P --> S <f3, c3>)

    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_predicate_term():
        # j1=M-->P, j2=S<->M
        result_statement = NALGrammar.StatementTerm(j2.statement.get_subject_term(),
                                                j1.statement.get_predicate_term(),
                                                j1.statement.get_copula())  # S-->P
    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1=M-->P, j2=M<->S
        result_statement = NALGrammar.StatementTerm(j2.statement.get_predicate_term(),
                                                j1.statement.get_predicate_term(),
                                                j1.statement.get_copula())  # S-->P
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1=P-->M, j2=S<->M
        result_statement = NALGrammar.StatementTerm(j1.statement.get_subject_term(),
                                                j2.statement.get_subject_term(),
                                                j1.statement.get_copula())  # P-->S
    elif j1.statement.get_predicate_term() == j2.statement.get_subject_term():
        # j1=P-->M, j2=M<->S
        result_statement = NALGrammar.StatementTerm(j1.statement.get_subject_term(),
                                                j2.statement.get_predicate_term(),
                                                j1.statement.get_copula())  # P-->S
    else:
        assert (
            False), "Error: Invalid inputs to nal_analogy: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

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
            f: and(f1,f2)

            c: and(or(f1,f2),c1,c2)
        Returns:
            :- Sentence (S <-> P <f3, c3>)
    """

    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_predicate_term():
        # j1=M<->P, j2=S<->M
        result_statement = NALGrammar.StatementTerm(j2.statement.get_subject_term(),
                                                j1.statement.get_predicate_term(),
                                                j1.statement.get_copula())  # S<->P
    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1=M<->P, j2=M<->S
        result_statement = NALGrammar.StatementTerm(j2.statement.get_predicate_term(),
                                                j1.statement.get_predicate_term(),
                                                j1.statement.get_copula())  # S<->P
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1=P<->M, j2=S<->M
        result_statement = NALGrammar.StatementTerm(j2.statement.get_subject_term(),
                                                j1.statement.get_subject_term(),
                                                j1.statement.get_copula())  # S<->P
    elif j1.statement.get_predicate_term() == j2.statement.get_subject_term():
        # j1=P<->M, j2=M<->S
        result_statement = NALGrammar.StatementTerm(j2.statement.get_predicate_term(),
                                                j2.statement.get_subject_term(),
                                                j1.statement.get_copula())  # S<->P
    else:
        assert (
            False), "Error: Invalid inputs to nal_resemblance: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    if isinstance(j1, NALGrammar.Judgment):
        # Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Resemblance(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def Abduction(j1, j2):
    """
        Abduction (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (P --> M <f1, c1>)

            j2: Sentence (S --> M <f2, c2>)
        Evidence:
            w+: and(f1,f2,c1,c2)

            w-: and(f1,c1,not(f2),c2)

            w: and(f1,c1,c2)
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    result_statement = NALGrammar.StatementTerm(j2.statement.get_subject_term(),
                                            j1.statement.get_subject_term(),
                                            j1.statement.get_copula())

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
        Induction (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M --> P <f1, c1>)

            j2: Sentence (M --> S <f2, c2>)
        Evidence:
            w+: and(f1,f2,c1,c2)

            w-: and(f2,c2,not(f1),c1)

            w: and(f2,c1,c2)
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
    # Statement
    result_statement = NALGrammar.StatementTerm(j2.statement.get_predicate_term(),
                                            j1.statement.get_predicate_term(), j1.statement.get_copula())

    if isinstance(j1, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Induction(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def Exemplification(j1, j2):
    """
        Exemplification (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (P --> M <f1, c1>)

            j2: Sentence (M --> S <f2, c2>)
        Evidence:
            w+: and(f1,c1,f2,c2)

            w-: 0

            w: w+
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
    # Statement
    result_statement = NALGrammar.StatementTerm(j2.statement.get_predicate_term(),
                                            j1.statement.get_subject_term(), j1.statement.get_copula())

    if isinstance(j1, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Exemplification(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)
    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


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
            w+: and(f1,c1,f2,c2)

            w: and(or(f1,f2),c1,c2)
        Returns:
            :- Sentence (S <-> P <f3, c3>)
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_subject_term():
        result_statement = NALGrammar.StatementTerm(j2.statement.get_predicate_term(),
                                                j1.statement.get_predicate_term(),
                                                NALSyntax.Copula.Similarity)
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        result_statement = NALGrammar.StatementTerm(j2.statement.get_subject_term(),
                                                j1.statement.get_subject_term(),
                                                NALSyntax.Copula.Similarity)
    else:
        assert (
            False), "Error: Invalid inputs to nal_comparison: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    if isinstance(j1, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Comparison(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result
