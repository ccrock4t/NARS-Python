"""
==== ==== ==== ==== ==== ====
==== NAL Inference Rules - Immediate Inference Rules ====
==== ==== ==== ==== ==== ====

    Author: Christian Hahm
    Created: October 8, 2020
    Purpose: Defines the NAL inference rules
            Assumes the given sentences do not have evidential overlap.
            Does combine evidential bases in the Resultant Sentence.
"""
import Global
import NALGrammar
import NALSyntax
from NALInferenceRules import TruthValueFunctions
from NALInferenceRules.HelperFunctions import create_resultant_sentence_one_premise


def Negation(j):
    """
         Negation

         -----------------

         Input:
           j: Sentence (Statement <f, c>)

         Returns:
    """
    NALGrammar.assert_sentence(j)
    result_statement = NALGrammar.StatementTerm(j.statement, statement_connector=NALSyntax.TermConnector.Negation)
    return create_resultant_sentence_one_premise(j, result_statement, TruthValueFunctions.F_Negation)


def Conversion(j):
    """
        Conversion Rule

        Reverses the subject and predicate.
        -----------------

        Input:
            j: Sentence (S --> P <f1, c1>)

            must have a frequency above zero, or else the confidence of the conclusion will be zero

        Truth Val:
            w+: and(f1,c1)
            w-: 0
        Returns:
            :- Sentence (P --> S <f2, c2>)
    """
    NALGrammar.assert_sentence(j)
    # Statement
    result_statement = NALGrammar.StatementTerm(j.statement.get_predicate_term(),
                                            j.statement.get_subject_term(),
                                            j.statement.get_copula())


    truth_function = TruthValueFunctions.TruthValueFunctions.F_Conversion

    return create_resultant_sentence_one_premise(j,result_statement,truth_function)


def Contraposition(j):
    """
    Contraposition
    Inputs:
      j: (S ==> P)

    Frequency must be below one or confidence of conclusion will be zero

    :param j:
    :return: ((--,P) ==> (--,S))
    """
    NALGrammar.assert_sentence(j)
    # Statement
    negated_predicate_term = NALGrammar.CompoundTerm([j.statement.get_predicate_term()],
                                                     NALSyntax.TermConnector.Negation)
    negated_subject_term = NALGrammar.CompoundTerm([j.statement.get_subject_term()],
                                                   NALSyntax.TermConnector.Negation)

    result_statement = NALGrammar.StatementTerm(negated_predicate_term,
                                            negated_subject_term,
                                            j.statement.get_copula())

    return create_resultant_sentence_one_premise(j, result_statement, TruthValueFunctions.F_Contraposition)


def ExtensionalImage(j):
    """
    Extensional Image
    Inputs:
      j: ((*,S,...,P) --> R)

    :param j:
    :returns: array of
    (S --> (/,R,_,...,P))
    (P --> (/,R,S,...,_))
    ...
    """
    NALGrammar.assert_sentence(j)

    results = []
    # Statement
    statement_subterms = j.statement.get_subject_term().subterms
    R = j.statement.get_predicate_term()

    for i1 in range(0, len(statement_subterms)):
        subterm = statement_subterms[i1]

        image_subterms = [R]
        for i2 in range(0, len(statement_subterms)):
            if i1 != i2:
                image_subterms.append(statement_subterms[i2])
            elif i1 == i2:
                image_subterms.append(Global.Global.TERM_IMAGE_PLACEHOLDER)

        image_term = NALGrammar.CompoundTerm(image_subterms,
                                             NALSyntax.TermConnector.ExtensionalImage)

        result_statement = NALGrammar.StatementTerm(subterm,
                                                image_term,
                                                NALSyntax.Copula.Inheritance)

        result = create_resultant_sentence_one_premise(j, result_statement, None)
        results.append(result)

    return results


def IntensionalImage(j):
    """
    Intensional Image
    Inputs:
      j: (R --> (*,S,P))

    :param j:
    :returns: array of
    ((/,R,_,P) --> S)
    and
    ((/,R,S,_) --> P)
    """
    NALGrammar.assert_sentence(j)

    results = []
    # Statement
    statement_subterms = j.statement.get_predicate_term().subterms
    R = j.statement.get_subject_term()

    for i1 in range(0, len(statement_subterms)):
        subterm = statement_subterms[i1]

        image_subterms = [R]
        for i2 in range(0, len(statement_subterms)):
            if i1 != i2:
                image_subterms.append(statement_subterms[i2])
            elif i1 == i2:
                image_subterms.append(Global.Global.TERM_IMAGE_PLACEHOLDER)

        image_term = NALGrammar.CompoundTerm(image_subterms,
                                             NALSyntax.TermConnector.ExtensionalImage)

        result_statement = NALGrammar.StatementTerm(image_term,
                                                subterm,
                                                NALSyntax.Copula.Inheritance)

        result = create_resultant_sentence_one_premise(j, result_statement, None)
        results.append(result)

    return results