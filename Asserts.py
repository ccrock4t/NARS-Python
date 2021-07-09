"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Enforces Narsese grammar that is used throughout the project
"""
import NALSyntax
import NALGrammar.Sentences
import NALGrammar.Terms
import NALGrammar.Values
import NARSDataStructures

def assert_sentence_forward_implication(j):
    """
        ==>, =/>, =\>
    :param j:
    :return:
    """
    assert_sentence(j)
    assert not NALSyntax.Copula.is_symmetric(j.statement.copula) and not NALSyntax.Copula.is_first_order(j.statement.copula), str(j) + " must be a forward implication statement"

def assert_sentence_asymmetric(j):
    """
        -->, ==>, =/>, =\>
    :param j:
    :return:
    """
    assert_sentence(j)
    assert not NALSyntax.Copula.is_symmetric(j.statement.copula), str(j) + " must be asymmetric"

def assert_sentence_symmetric(j):
    """
        <->,<=>,</>
    :param j:
    :return:
    """
    assert_sentence(j)
    assert NALSyntax.Copula.is_symmetric(j.statement.copula), str(j) + " must be symmetric"

def assert_sentence_equivalence(j):
    """
        <=> </>
    :param j:
    :return:
    """
    assert_sentence(j)
    assert NALSyntax.Copula.is_symmetric(j.statement.copula) and not NALSyntax.Copula.is_first_order(j.statement.copula), str(j) + " must be an equivalence statement"

def assert_sentence_similarity(j):
    """
        -->
    :param j:
    :return:
    """
    assert_sentence(j)
    assert j.statement.copula == NALSyntax.Copula.Similarity, str(j) + " must be a similarity statement"

def assert_sentence_inheritance(j):
    """
        -->
    :param j:
    :return:
    """
    assert_sentence(j)
    assert j.statement.copula == NALSyntax.Copula.Inheritance, str(j) + " must be an inheritance statement"

def assert_term(t):
    assert (isinstance(t, NALGrammar.Terms.Term)), str(t) + " must be a Term"


def assert_statement_term(t):
    assert (isinstance(t, NALGrammar.Terms.StatementTerm)), str(t) + " must be a Statement Term"


def assert_sentence(j):
    assert (isinstance(j, NALGrammar.Sentences.Sentence)), str(j) + " must be a Sentence"


def assert_truth_value(j):
    assert (isinstance(j, NALGrammar.Values.TruthValue)), str(j) + " must be a TruthValue"


def assert_punctuation(j):
    assert (isinstance(j, NALSyntax.Punctuation)), str(j) + " must be a Punctuation"


def assert_copula(j):
    assert (isinstance(j, NALSyntax.Copula)), str(j) + " must be a Copula"

def assert_task(j):
    assert (isinstance(j, NARSDataStructures.Task)), str(j) + " must be a Task"
