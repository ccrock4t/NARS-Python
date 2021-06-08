"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Enforces Narsese grammar that is used throughout the project
"""
import NALSyntax
import NALGrammar.Sentence
import NALGrammar.Term
import NALGrammar.Value


def assert_term(t):
    assert (isinstance(t, NALGrammar.Term.Term)), str(t) + " must be a Term"


def assert_statement_term(t):
    assert (isinstance(t, NALGrammar.Term.StatementTerm)), str(t) + " must be a Statement Term"


def assert_sentence(j):
    assert (isinstance(j, NALGrammar.Sentence.Sentence)), str(j) + " must be a Sentence"


def assert_truth_value(j):
    assert (isinstance(j, NALGrammar.Value.TruthValue)), str(j) + " must be a TruthValue"


def assert_punctuation(j):
    assert (isinstance(j, NALSyntax.Punctuation)), str(j) + " must be a Punctuation"


def assert_copula(j):
    assert (isinstance(j, NALSyntax.Copula)), str(j) + " must be a Copula"
