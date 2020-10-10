from NALSyntax import *


# Term Copula Term Punctuation <f, c>
class Sentence:

    def __init__(self, statement, truth_value, punctuation):
        assert(isinstance(statement, Statement)), "Statement must be a Statement"
        assert (isinstance(truth_value, TruthValue)), "Truth value must be a TruthValue"
        assert (isinstance(punctuation, Punctuation)), "Punctuation must be a Punctuation"

        self.statement = statement
        self.truthValue = truth_value
        self.punctuation = punctuation

    def __str__(self):
        return str(self.statement) + str(self.punctuation.value) + " " + str(self.truthValue)


# Term Copula Term
class Statement:
    def __init__(self, subjectPredicate, copula):
        assert(isinstance(subjectPredicate, SubjectPredicate)), "subjectPredicate must be a SubjectPredicate"
        assert (isinstance(copula, Copula)), "Copula must be a Copula"

        self.subjectPredicate = subjectPredicate
        self.copula = copula
        self.term = StatementTerm(subjectPredicate.subject, subjectPredicate.predicate, copula)

    def __str__(self):
        return str(StatementSyntax.Start.value) \
               + str(self.subjectPredicate.subject) \
               + " " + str(self.copula.value) + " " \
               + str(self.subjectPredicate.predicate) \
               + str(StatementSyntax.End.value)


class TruthValue:
    def __init__(self, frequency, confidence):
        assert(isinstance(frequency, float)), "Frequency must be a float"
        assert (isinstance(confidence, float)), "Confidence must be a float"
        self.frequency = frequency
        self.confidence = confidence

    def __str__(self):
        return str(StatementSyntax.TruthValMarker.value) \
               + "{:.2f}".format(self.frequency) \
               + str(StatementSyntax.TruthValDivider.value) \
               + "{:.2f}".format(self.confidence) \
               + str(StatementSyntax.TruthValMarker.value)


class SubjectPredicate:
    def __init__(self, subject, predicate):
        assert(isinstance(subject, Term)), "Subject must be a Term"
        assert (isinstance(predicate, Term)), "Predicate must be a Term"
        self.subject = subject
        self.predicate = predicate


class Term:
    def __init__(self, termString):
        assert (isinstance(termString, str)), "termString must be a str"
        self.string = termString

    def __str__(self):
        return self.string

    def __eq__(self, other):
        if isinstance(other, Term):
            return str(self) == str(other)
        return False

    def __hash__(self):
        return hash(str(self))


# (Connector T1, T2, ..., Tn)
class CompoundTerm(Term):
    # subterms = array of terms or compound terms
    # connector = Connector
    def __init__(self, subterms, connector):
        self.subterms = subterms
        self.connector = connector
        super().__init__(self.get_string())

    def get_string(self):
        str = self.connector
        for subterm in self.subterms:
            str = str + "," + subterm
        return "(" + str + ")"


# SubjectTerm Copula PredicateTerm
class StatementTerm(CompoundTerm):
    # subject term
    # predicate term
    # copula
    def __init__(self, subject, predicate, copula):
        assert_term(subject)
        assert_term(predicate)
        assert(isinstance(copula, Copula)), "Copula must be a Copula"
        super().__init__([subject, predicate], copula)

    def get_subject(self):
        return self.subterms[0]

    def get_predicate(self):
        return self.subterms[1]

    def get_string(self):
        string = str(self.get_subject()) + "," + str(self.get_predicate())
        return "(" + string + ")"

def assert_term(t):
    assert (isinstance(t, Term)), str(t) + " must be a Term"

def assert_sentence(j):
    assert (isinstance(j, Sentence)), str(j) + " must be a Sentence"