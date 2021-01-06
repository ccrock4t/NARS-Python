from NALSyntax import *
"""
    Author: Christian Hahm
    Created: October 9, 2020
"""
class Sentence:
    """
        <Statement><Punctuation> <value>
    """
    def __init__(self, statement, value, punctuation):
        assert_statement(statement)
        assert_punctuation(punctuation)

        self.statement = statement
        self.value = value
        self.punctuation = punctuation

    def get_formatted_string(self):
        return self.statement.get_formatted_string() + str(self.punctuation.value) + " " + self.value.get_formatted_string()

class Judgment(Sentence):
    """
        <Statement>. <truth-value>
    """
    def __init__(self, statement, value):
        assert_statement(statement)
        assert_truth_value(value)
        super().__init__(statement, value, Punctuation.Judgment)

class Statement:
    """
        <Term Copula Term>
    """
    def __init__(self, subject_predicate, copula):
        assert_subject_predicate(subject_predicate)
        assert_copula(copula)

        self.subject_predicate = subject_predicate
        self.copula = copula
        self.term = StatementTerm(subject_predicate.subject_term, subject_predicate.predicate_term, copula)

    def get_formatted_string(self):
        return str(StatementSyntax.Start.value) \
               + self.subject_predicate.subject_term.get_formatted_string() \
               + " " + str(self.copula.value) + " " \
               + self.subject_predicate.predicate_term.get_formatted_string() \
               + str(StatementSyntax.End.value)

class EvidentialValue:
    """
        <frequency, confidence>
    """
    def __init__(self, frequency, confidence):
        assert(isinstance(frequency, float)), "frequency must be a float"
        assert (isinstance(confidence, float)), "confidence must be a float"
        self.frequency = frequency
        self.confidence = confidence

    def get_formatted_string(self):
        return str(StatementSyntax.TruthValMarker.value) \
               + "{:.2f}".format(self.frequency) \
               + str(StatementSyntax.TruthValDivider.value) \
               + "{:.2f}".format(self.confidence) \
               + str(StatementSyntax.TruthValMarker.value)

class DesireValue(EvidentialValue):
    """
        <frequency, confidence>
        Describing S ==> D,
        how much the associated statement S implies the overall desired state of NARS, D
    """
    def __init__(self, frequency, confidence):
        super().__init__(frequency=frequency, confidence=confidence)


class TruthValue(EvidentialValue):
    """
        <frequency, confidence> <tense> <timestamp>
        Describing the evidential basis for the associated statement to be true
    """
    def __init__(self, frequency, confidence, tense=None):
        self.tense = tense
        super().__init__(frequency=frequency, confidence=confidence)


class SubjectPredicate:
    """
        An object that holds a subject and predicate term
    """
    def __init__(self, subject, predicate):
        assert_term(subject)
        assert_term(predicate)
        self.subject_term = subject
        self.predicate_term = predicate


class Term:
    """
        A valid word.

        Base class for all terms, and can be used for Atomic terms
    """
    def __init__(self, term_string):
        assert (isinstance(term_string, str)), term_string + " must be a str"
        self.string = term_string

    def get_formatted_string(self):
        return self.string

    def __eq__(self, other):
        if isinstance(other, Term):
            return str(self) == str(other)
        return False

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return self.get_formatted_string()



class CompoundTerm(Term):
    """
        A term that contains multiple atomic subterms.

        (Connector T1, T2, ..., Tn)
    """
    def __init__(self, subterms, connector):
        """
        Input:
            subterms: array of terms or compound terms

            connector: Connector
        """
        for subterm in subterms:
            assert_term(subterm)
        self.subterms = subterms
        self.connector = connector
        super().__init__(self.get_formatted_string())

    def get_formatted_string(self):
        str = self.connector
        for subterm in self.subterms:
            str = str + "," + subterm

        return "(" + str + ")"


class StatementTerm(CompoundTerm):
    """
        A special kind of compound term with a subject, predicate, and copula

        P --> Q
    """
    def __init__(self, subject, predicate, copula):
        assert_term(subject)
        assert_term(predicate)
        assert_copula(copula)
        super().__init__([subject, predicate], copula)

    def get_subject_term(self):
        return self.subterms[0]

    def get_predicate_term(self):
        return self.subterms[1]

    def get_copula_string(self):
        return str(self.connector.value)

    def get_formatted_string(self):
        string = self.get_subject_term().get_formatted_string() + self.get_copula_string() + self.get_predicate_term().get_formatted_string()
        return "(" + string + ")"

def assert_term(t):
    assert (isinstance(t, Term)), str(t) + " must be a Term"

def assert_statement_term(t):
    assert (isinstance(t, StatementTerm)), str(t) + " must be a Statement Term"

def assert_sentence(j):
    assert (isinstance(j, Sentence)), str(j) + " must be a Sentence"

def assert_statement(j):
    assert (isinstance(j, Statement)), str(j) + " must be a Statement"

def assert_truth_value(j):
    assert (isinstance(j, TruthValue)), str(j) + " must be a TruthValue"

def assert_punctuation(j):
    assert (isinstance(j, Punctuation)), str(j) + " must be a Punctuation"

def assert_subject_predicate(j):
    assert (isinstance(j, SubjectPredicate)), str(j) + " must be a SubjectPredicate"

def assert_copula(j):
    assert (isinstance(j, Copula)), str(j) + " must be a Copula"