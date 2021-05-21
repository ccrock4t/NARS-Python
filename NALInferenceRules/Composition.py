"""
==== ==== ==== ==== ==== ====
==== NAL Inference Rules - Composition Inference Rules ====
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


def IntensionalIntersectionOrDisjunction(j1, j2):
    """
        First Order: Intensional Intersection (Strong Inference)
        Higher Order: Disjunction

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (T1 --> M <f1, c1>) (Sentence (T1 ==> M <f1, c1>))
            and
            j2: Sentence (T2 --> M <f2, c2>) (Sentence (T2 ==> M <f2, c2>))

            OR

            j1: Sentence (M --> T1 <f1, c1>) (Sentence (M ==> T1 <f1, c1>))
            and
            j2: Sentence (M --> T2 <f2, c2>) (Sentence (M ==> T2 <f2, c2>))
        Evidence:
            F_int

            OR

            F_uni
        Returns:
            :- Sentence ((T1 | T2) --> M) (Sentence ((T1 || T2) --> M))
            OR
            :- Sentence (M --> (T1 | T2)) (Sentence (M --> (T1 || T2)))
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    j1_copula = j1.statement.get_copula()
    j2_copula = j2.statement.get_copula()
    # Statement
    connector = None
    copula = None
    if NALSyntax.Copula.is_first_order(j1_copula) and NALSyntax.Copula.is_first_order(j2_copula):
        connector = NALSyntax.TermConnector.IntensionalIntersection
        copula = NALSyntax.Copula.Inheritance
    else:
        # higher-order, could be temporal
        # todo temporal disjunction
        connector = NALSyntax.TermConnector.Disjunction
        copula = NALSyntax.Copula.Implication

    # Statement
    result_truth = None
    if j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1: Sentence(T1 --> M < f1, c1 >)
        # j2: Sentence(T2 --> M < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_subject_term(),
                                                 j2.statement.get_subject_term()],
                                                term_connector=connector)  # (T1 & T2)
        result_statement = NALGrammar.Statement(compound_term,
                                                j1.statement.get_predicate_term(),
                                                copula)  # ((T1 | T2) --> M)

        if isinstance(j1, NALGrammar.Judgment):
            # Get Truth Value
            (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
            result_truth = TruthValueFunctions.F_Intersection(f1, c1, f2, c2)

    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1: Sentence(M --> T1 < f1, c1 >)
        # j2: Sentence(M --> T2 < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_predicate_term(),
                                                 j2.statement.get_predicate_term()],
                                                term_connector=connector)  # (T1 & T2)

        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                compound_term,
                                                copula)  # (M --> (T1 | T2))

        if isinstance(j1, NALGrammar.Judgment):
            # Get Truth Value
            (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
            result_truth = TruthValueFunctions.F_Union(f1, c1, f2, c2)

    if isinstance(j1, NALGrammar.Judgment):
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def ExtensionalIntersectionOrConjunction(j1, j2):
    """
        First-Order: Extensional Intersection (Strong Inference)
        Higher-Order: Conjunction

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (T1 --> M <f1, c1>) (Sentence (T1 ==> M <f1, c1>))
            and
            j2: Sentence (T2 --> M <f2, c2>) (Sentence (T2 ==> M <f2, c2>))

            OR

            j1: Sentence (M --> T1 <f1, c1>) (Sentence (M ==> T1 <f1, c1>))
            and
            j2: Sentence (M --> T2 <f2, c2>) (Sentence (M ==> T2 <f2, c2>))
        Evidence:
            F_uni

            OR

            F_int
        Returns:
            :- Sentence ((T1 & T2) --> M) (Sentence ((T1 && T2) ==> M))
            OR
            :- Sentence (M --> (T1 & T2)) (Sentence (M ==> (T1 && T2)))
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    j1_copula = j1.statement.get_copula()
    j2_copula = j2.statement.get_copula()
    # Statement
    connector = None
    copula = None
    if NALSyntax.Copula.is_first_order(j1_copula) and NALSyntax.Copula.is_first_order(j2_copula):
        connector = NALSyntax.TermConnector.ExtensionalIntersection
        copula = NALSyntax.Copula.Inheritance
    else:
        # higher-order, could be temporal
        # todo temporal conjunction
        connector = NALSyntax.TermConnector.Conjunction
        copula = NALSyntax.Copula.Implication

    result_truth = None
    if j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1: Sentence(T1 --> M < f1, c1 >)
        # j2: Sentence(T2 --> M < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_subject_term(),
                                                 j2.statement.get_subject_term()],
                                                term_connector=connector)  # (T1 & T2)
        result_statement = NALGrammar.Statement(compound_term,
                                                j1.statement.get_predicate_term(),
                                                copula)  # ((T1 & T2) --> M)

        if isinstance(j1, NALGrammar.Judgment):
            # Get Truth Value
            (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
            result_truth = TruthValueFunctions.F_Union(f1, c1, f2, c2)

    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1: Sentence(M --> T1 < f1, c1 >)
        # j2: Sentence(M --> T2 < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_predicate_term(),
                                                 j2.statement.get_predicate_term()],
                                                term_connector=connector)  # (T1 & T2)
        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                compound_term,
                                                copula)  # (M --> (T1 & T2))

        if isinstance(j1, NALGrammar.Judgment):
            # Get Truth Value
            (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
            result_truth = TruthValueFunctions.F_Intersection(f1, c1, f2, c2)

    if isinstance(j1, NALGrammar.Judgment):
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def IntensionalDifference(j1, j2):
    """
        Intensional Difference (Strong Inference)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (T1 --> M <f1, c1>)
            and
            j2: Sentence (T2 --> M <f2, c2>)
        Evidence:
            F_difference
        Returns:
            :- Sentence ((T1 ~ T2) --> M)
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
    assert j1.statement.get_predicate_term() == j2.statement.get_predicate_term()

    compound_term = NALGrammar.CompoundTerm([j1.statement.get_predicate_term(),
                                             j2.statement.get_predicate_term()],
                                            NALSyntax.TermConnector.ExtensionalDifference)  # (T1 - T2)
    result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                            compound_term,
                                            NALSyntax.Copula.Inheritance)  # (M --> (T1 - T2))

    if isinstance(j1, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Difference(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def ExtensionalDifference(j1, j2):
    """
        Extensional Difference (Strong Inference)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------
        Input:
            j1: Sentence (M --> T1 <f1, c1>)
            and
            j2: Sentence (M --> T2 <f2, c2>)
        Evidence:
            F_difference
        Returns:
            :- Sentence (M --> (T1 - T2))
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    if j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1: Sentence(T1 --> M < f1, c1 >)
        # j2: Sentence(T2 --> M < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_subject_term(),
                                                 j2.statement.get_subject_term()],
                                                NALSyntax.TermConnector.IntensionalDifference)
        result_statement = NALGrammar.Statement(compound_term,
                                                j1.statement.get_predicate_term(),
                                                NALSyntax.Copula.Inheritance)  # ((T1 ~ T2) --> M)

    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1: Sentence(M --> T1 < f1, c1 >)
        # j2: Sentence(M --> T2 < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_predicate_term(),
                                                 j2.statement.get_predicate_term()],
                                                NALSyntax.TermConnector.ExtensionalDifference)
        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                compound_term,
                                                NALSyntax.Copula.Inheritance)  # (M --> (T1 - T2))

    if isinstance(j1, NALGrammar.Judgment):
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = TruthValueFunctions.F_Difference(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time=j1.stamp.occurrence_time)
    elif isinstance(j1, NALGrammar.Question):
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result