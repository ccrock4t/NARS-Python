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
import Asserts
import NALGrammar
import NALSyntax
from NALInferenceRules import TruthValueFunctions, HelperFunctions


def DisjunctionOrIntensionalIntersection(j1, j2):
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
    Asserts.assert_sentence_asymmetric(j1)
    Asserts.assert_sentence_asymmetric(j2)

    # Statement
    connector = None
    copula = None
    if j1.statement.is_first_order() and j2.statement.is_first_order():
        connector = NALSyntax.TermConnector.IntensionalIntersection
        copula = NALSyntax.Copula.Inheritance
    else:
        # higher-order, could be temporal
        # todo temporal disjunction
        connector = NALSyntax.TermConnector.Disjunction
        copula = NALSyntax.Copula.Implication

    # Statement
    result_truth_function = None
    if j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1: Sentence(T1 --> M < f1, c1 >)
        # j2: Sentence(T2 --> M < f2, c2 >)
        if isinstance(j1.statement.get_subject_term(), NALGrammar.Terms.CompoundTerm) \
                or isinstance(j2.statement.get_subject_term(), NALGrammar.Terms.CompoundTerm):
            # don't compound terms which are already compound
            # this reduces complexity.
            # todo: better simplifying of syntactically complex results
            return None

        compound_term = NALGrammar.Terms.CompoundTerm([j1.statement.get_subject_term(),
                                                       j2.statement.get_subject_term()],
                                                      term_connector=connector)  # (T1 | T2)
        result_statement = NALGrammar.Terms.StatementTerm(compound_term,
                                                          j1.statement.get_predicate_term(),
                                                          copula)  # ((T1 | T2) --> M)

        if not isinstance(j1, NALGrammar.Sentences.Question):
            result_truth_function = TruthValueFunctions.F_Intersection

    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1: Sentence(M --> T1 < f1, c1 >)
        # j2: Sentence(M --> T2 < f2, c2 >)
        if isinstance(j1.statement.get_predicate_term(), NALGrammar.Terms.CompoundTerm) \
                or isinstance(j2.statement.get_predicate_term(), NALGrammar.Terms.CompoundTerm):
            # don't compound terms which are already compound
            # this reduces complexity.
            # todo: better simplifying of syntactically complex results
            return None

        compound_term = NALGrammar.Terms.CompoundTerm([j1.statement.get_predicate_term(),
                                                       j2.statement.get_predicate_term()],
                                                      term_connector=connector)  # (T1 | T2)

        result_statement = NALGrammar.Terms.StatementTerm(j1.statement.get_subject_term(),
                                                          compound_term,
                                                          copula)  # (M --> (T1 | T2))

        if not isinstance(j1, NALGrammar.Sentences.Question):
            result_truth_function = TruthValueFunctions.F_Union
    else:
        assert False,"ERROR: Invalid inputs to Intensional Intersection"

    return HelperFunctions.create_resultant_sentence_two_premise(j1,
                                                                 j2,
                                                                 result_statement,
                                                                 result_truth_function)


def ConjunctionOrExtensionalIntersection(j1, j2):
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
            Sentence ((T1 & T2) --> M) or Sentence ((T1 && T2) ==> M)

            or

            Sentence (M --> (T1 & T2)) or Sentence (M ==> (T1 && T2))
    """
    Asserts.assert_sentence_asymmetric(j1)
    Asserts.assert_sentence_asymmetric(j2)

    # Statement
    connector = None
    copula = None
    if j1.statement.is_first_order() and j2.statement.is_first_order():
        connector = NALSyntax.TermConnector.ExtensionalIntersection # &
        copula = NALSyntax.Copula.Inheritance
    else:
        # higher-order, could be temporal
        connector = NALSyntax.TermConnector.Conjunction # &&
        copula = NALSyntax.Copula.Implication

    result_truth_function = None
    if j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1: Sentence(T1 --> M < f1, c1 >)
        # j2: Sentence(T2 --> M < f2, c2 >)
        if isinstance(j1.statement.get_subject_term(), NALGrammar.Terms.CompoundTerm) \
                or isinstance(j2.statement.get_subject_term(), NALGrammar.Terms.CompoundTerm):
            # don't compound terms which are already compound
            # this reduces complexity.
            # todo: better simplifying of syntactically complex results
            return None

        compound_term = NALGrammar.Terms.CompoundTerm([j1.statement.get_subject_term(),
                                                       j2.statement.get_subject_term()],
                                                      term_connector=connector)  # (T1 & T2)
        result_statement = NALGrammar.Terms.StatementTerm(compound_term,
                                                          j1.statement.get_predicate_term(),
                                                          copula)  # ((T1 & T2) --> M)

        if not isinstance(j1, NALGrammar.Sentences.Question):
            result_truth_function = TruthValueFunctions.F_Union

    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1: Sentence(M --> T1 < f1, c1 >)
        # j2: Sentence(M --> T2 < f2, c2 >)
        if isinstance(j1.statement.get_predicate_term(), NALGrammar.Terms.CompoundTerm) \
                or isinstance(j2.statement.get_predicate_term(), NALGrammar.Terms.CompoundTerm):
            # don't compound terms which are already compound
            # this reduces complexity.
            # todo: better simplifying of syntactically complex results
            return None
        compound_term = NALGrammar.Terms.CompoundTerm([j1.statement.get_predicate_term(),
                                                       j2.statement.get_predicate_term()],
                                                      term_connector=connector)  # (T1 & T2)
        result_statement = NALGrammar.Terms.StatementTerm(j1.statement.get_subject_term(),
                                                          compound_term,
                                                          copula)  # (M --> (T1 & T2))

        if not isinstance(j1, NALGrammar.Sentences.Question):
            result_truth_function = TruthValueFunctions.F_Intersection
    else:
        assert False, "ERROR: Invalid inputs to Extensional Intersection"

    return HelperFunctions.create_resultant_sentence_two_premise(j1,
                                                                 j2,
                                                                 result_statement,
                                                                 result_truth_function)


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
    Asserts.assert_sentence_asymmetric(j1)
    Asserts.assert_sentence_asymmetric(j2)
    assert j1.statement.get_predicate_term() == j2.statement.get_predicate_term()

    if isinstance(j1.statement.get_subject_term(), NALGrammar.Terms.CompoundTerm) \
            or isinstance(j2.statement.get_subject_term(), NALGrammar.Terms.CompoundTerm):
        # don't compound terms which are already compound
        # this reduces complexity.
        # todo: better simplifying of syntactically complex results
        return None

    compound_term = NALGrammar.Terms.CompoundTerm([j1.statement.get_subject_term(),
                                                   j2.statement.get_subject_term()],
                                                  NALSyntax.TermConnector.IntensionalDifference)  # (T1 ~ T2)
    result_statement = NALGrammar.Terms.StatementTerm(compound_term,
                                                      j1.statement.get_predicate_term(),
                                                      NALSyntax.Copula.Inheritance)  # ((T1 ~ T2) --> M)
    return HelperFunctions.create_resultant_sentence_two_premise(j1,
                                                                 j2,
                                                                 result_statement,
                                                                 TruthValueFunctions.F_Difference)


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
    Asserts.assert_sentence_asymmetric(j1)
    Asserts.assert_sentence_asymmetric(j2)
    assert j1.statement.get_subject_term() == j2.statement.get_subject_term()

    if isinstance(j1.statement.get_predicate_term(), NALGrammar.Terms.CompoundTerm) \
            or isinstance(j2.statement.get_predicate_term(), NALGrammar.Terms.CompoundTerm):
        # don't compound terms which are already compound
        # this reduces complexity.
        # todo: better simplifying of syntactically complex results
        return None

    compound_term = NALGrammar.Terms.CompoundTerm([j1.statement.get_predicate_term(),
                                                   j2.statement.get_predicate_term()],
                                                  NALSyntax.TermConnector.ExtensionalDifference)
    result_statement = NALGrammar.Terms.StatementTerm(j1.statement.get_subject_term(),
                                                      compound_term,
                                                      NALSyntax.Copula.Inheritance)  # (M --> (T1 - T2))

    return HelperFunctions.create_resultant_sentence_two_premise(j1,
                                                                 j2,
                                                                 result_statement,
                                                                 TruthValueFunctions.F_Difference)