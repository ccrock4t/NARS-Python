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

    def get_formatted_string(self):
        return self.statement.get_formatted_string() + str(self.punctuation.value) + " " + self.truthValue.get_formatted_string()


# Term Copula Term
class Statement:
    def __init__(self, subjectPredicate, copula):
        assert(isinstance(subjectPredicate, SubjectPredicate)), "subjectPredicate must be a SubjectPredicate"
        assert (isinstance(copula, Copula)), "copula must be a Copula"

        self.subjectPredicate = subjectPredicate
        self.copula = copula
        self.term = StatementTerm(subjectPredicate.subject, subjectPredicate.predicate, copula)

    def get_formatted_string(self):
        return str(StatementSyntax.Start.value) \
               + self.subjectPredicate.subject.get_formatted_string() \
               + " " + str(self.copula.value) + " " \
               + self.subjectPredicate.predicate.get_formatted_string() \
               + str(StatementSyntax.End.value)


class TruthValue:
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


class SubjectPredicate:
    def __init__(self, subject, predicate):
        assert(isinstance(subject, Term)), "subject must be a Term"
        assert (isinstance(predicate, Term)), "predicate must be a Term"
        self.subject = subject
        self.predicate = predicate


class Term:
    def __init__(self, termString):
        assert (isinstance(termString, str)), termString + " must be a str"
        self.string = termString

    def get_formatted_string(self):
        return self.string

    def __eq__(self, other):
        if isinstance(other, Term):
            return str(self) == str(other)
        return False

    def __hash__(self):
        return hash(str(self))


# (Connector T1, T2, ..., Tn)
class CompoundTerm(Term):

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
    def __init__(self, subject, predicate, copula):
        assert_term(subject)
        assert_term(predicate)
        assert(isinstance(copula, Copula)), "Copula must be a Copula"
        super().__init__([subject, predicate], copula)

    def get_subject(self):
        return self.subterms[0]

    def get_predicate(self):
        return self.subterms[1]

    def get_copula_string(self):
        return str(self.connector.value)

    def get_formatted_string(self):
        string = self.get_subject().get_formatted_string() + self.get_copula_string() + self.get_predicate().get_formatted_string()
        return "(" + string + ")"

def assert_term(t):
    assert (isinstance(t, Term)), str(t) + " must be a Term"

def assert_sentence(j):
    assert (isinstance(j, Sentence)), str(j) + " must be a Sentence"