import Global
import NALSyntax
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
        self.value = value # truth-value or desire-value
        self.punctuation = punctuation
        self.stamp = Sentence.Stamp()

    def get_formatted_string(self):
        return self.statement.get_formatted_string() + str(self.punctuation.value) + " " + self.value.get_formatted_string()

    class Stamp():
        def __init__(self):
            self.id = -1
            self.creation_time = Global.current_cycle_number # when was stamp created (in inference cycles)?
            self.occurrence_time = -1 # when did this statement occur (in inference cycles)
            self.syntactic_complexity = -1 # number of subterms
            self.evidential_base = Sentence.EvidentialBase(self.id)

    class EvidentialBase:
        def __init__(self, id):
            self.evidential_base = [id] # how was the sentence derived?

        def merge_evidential_base_into_self(self, other_base):
            new_basis = [self.evidential_base[:], other_base[:]] # merge both bases
            self.evidential_base = new_basis

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
    def __init__(self, subject, predicate, copula):
        assert_term(subject)
        assert_term(predicate)
        assert_copula(copula)

        self.subject_term = subject
        self.predicate_term = predicate
        self.copula = copula
        self.term = StatementTerm(subject, predicate, copula)

    def get_formatted_string(self):
        return str(StatementSyntax.Start.value) \
               + self.subject_term.get_formatted_string() \
               + " " + str(self.copula.value) + " " \
               + self.predicate_term.get_formatted_string() \
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

class Term:
    """
        A valid word.

        Base class for all terms. Use to create any term
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

class AtomicTerm(Term):
    """
        An atomic term

        T
    """
    def __init__(self, term_string):
        """
        Input:
            subterms: array of terms or compound terms

            connector: Connector
        """
        assert(AtomicTerm.is_valid_term(term_string)), term_string + " is not a valid Atomic Term name."
        super().__init__(term_string)

    @classmethod
    def is_valid_term(cls, term_string):
        return term_string in NALSyntax.valid_term_chars


class CompoundTerm(Term):
    """
        A term that contains multiple atomic subterms connected by a connector (including copula).

        (Connector T1, T2, ..., Tn)
    """
    def __init__(self, subterms, connector):
        """
        Input:
            subterms: array of immediate subterms

            connector: subterm connector
        """
        self.subterms = subterms
        self.connector = connector
        super().__init__(self.get_formatted_string())

    @classmethod
    def from_string(cls, compound_term_string):
        """
            Create a compound term from a string representing a compound term
        """
        subterms, connector = cls.parse_toplevel_subterms_and_connector(compound_term_string)
        return cls(subterms, connector)

    @classmethod
    def parse_toplevel_subterms_and_connector(cls, compound_term_string):
        """
            Parse out all top-level subterms from a string representing a compound term

            compound_term_string - a string representing a compound term
        """
        subterms = []
        internal_string = compound_term_string[1:len(compound_term_string) - 1]
        connector = StatementConnector.get_statement_connector_from_string(internal_string[0:2])

        if connector is None:
            connector = TermConnector.get_term_connector_from_string(internal_string[0])

        assert(connector is not None), "Connector could not be parsed from CompoundTerm string."
        assert (internal_string[len(connector.value)] == ','), "Connector not followed by comma in CompoundTerm string."

        internal_terms_string = internal_string[len(connector.value)+1:]

        depth = 0
        subterm_string = ""
        for i, c in enumerate(internal_terms_string):
            if c == StatementSyntax.Start_Alternate.value or c == StatementSyntax.Start.value:
                depth = depth + 1
            elif c == StatementSyntax.End_Alternate.value:
                depth = depth - 1

            if depth == 0:
                if c == ",":
                    subterm_string = subterm_string.strip()
                    subterms.append(MakeTermFromString(subterm_string))
                    subterm_string = ""
                else:
                    subterm_string = subterm_string + c

        subterm_string = subterm_string.strip()
        subterms.append(MakeTermFromString(subterm_string))

        return subterms, connector

    def get_formatted_string(self):
        string = self.connector.value
        for subterm in self.subterms:
            string = string + "," + str(subterm)

        return "(" + string + ")"


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

    @classmethod
    def from_string(cls, term_string):
        subject, predicate, connector, _ = parse_subject_predicate_copula_and_copula_index(term_string)
        return cls(subject, predicate, connector)

    def get_subject_term(self):
        return self.subterms[0]

    def get_predicate_term(self):
        return self.subterms[1]

    def get_copula_string(self):
        return str(self.connector.value)

    def get_formatted_string(self):
        string = self.get_subject_term().get_formatted_string() + self.get_copula_string() + self.get_predicate_term().get_formatted_string()
        return "(" + string + ")"

def MakeTermFromString(term_string):
    """
        either an atomic term, or a statement/compound term surrounded in parentheses.
    """
    if term_string[0] == "(":
        assert(term_string[len(term_string) - 1] == ")"), "Compound term must have ending parenthesis"
        term_connector = TermConnector.get_term_connector_from_string(term_string[1]) # ex: (*,t1,t2)
        statement_connector = StatementConnector.get_statement_connector_from_string(term_string[0:2]) # ex: (&&,t1,t2)
        if term_connector is None and statement_connector is None:
            # statement term
            term = StatementTerm.from_string(term_string)
        else:
            # compound term
            term = CompoundTerm.from_string(term_string)
    else:
        term = AtomicTerm(term_string)

    return term

def parse_subject_predicate_copula_and_copula_index(statement_string):
    """
    Parameter: statement_string - String of NAL syntax <term copula term> or (term copula term)

    Returns: top-level subject term, predicate term, copula, copula index
    """
    print(statement_string)
    # get copula
    copula = -1
    copula_idx = -1
    depth = 0
    for i, v in enumerate(statement_string):
        print(v)
        if v == StatementSyntax.Start_Alternate.value or v == StatementSyntax.Start.value:
            depth = depth + 1
        elif v == StatementSyntax.End_Alternate.value:
            depth = depth - 1
        elif depth == 1 and i + 3 <= len(statement_string) and Copula.is_string_a_copula(statement_string[i:i + 3]):
            copula, copula_idx = Copula.get_copula_from_string(statement_string[i:i + 3]), i
        print(depth)

    assert (copula_idx != -1), "Copula not found. Exiting.."

    subject_str = statement_string[1:copula_idx].strip() # get subject string
    predicate_str = statement_string[copula_idx + len(copula.value):len(statement_string)-1].strip() #get predicate string

    return MakeTermFromString(subject_str), MakeTermFromString(predicate_str), copula, copula_idx

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

def assert_copula(j):
    assert (isinstance(j, Copula)), str(j) + " must be a Copula"