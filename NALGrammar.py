import Config
from Global import Global
from NALSyntax import *

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Enforces Narsese grammar that is used throughout the project
"""


class Sentence:
    """
        sentence ::= <statement><punctuation> %<value>%G
    """
    def __init__(self, statement, value, punctuation):
        assert_statement(statement)
        assert_punctuation(punctuation)

        self.statement: Statement = statement
        self.value: EvidentialValue = value  # truth-value (for Judgment) or desire-value (for Goal) or None (for Question)
        self.punctuation: Punctuation = punctuation
        self.stamp: Sentence.Stamp = Sentence.Stamp()

    def __str__(self):
        return self.get_formatted_string()

    def has_evidential_overlap(self, sentence):
        assert_sentence(sentence)
        return self.stamp.evidential_base.has_evidential_overlap(sentence.stamp.evidential_base)

    def get_formatted_string(self):
        string = Global.ID_MARKER + str(self.stamp.id) + Global.ID_END_MARKER
        string = string + self.statement.get_formatted_string() + str(self.punctuation.value)
        if self.value is not None: string = string + " " + self.value.get_formatted_string()
        return string

    def get_formatted_string_no_id(self):
        string = self.statement.get_formatted_string() + str(self.punctuation.value)
        if self.value is not None: string = string + " " + self.value.get_formatted_string()
        return string

    class Stamp:
        """
            (id, tcr, toc, C, E) ∈ N×N×N×N×P(N)
            where 'id' represents a unique ID
            'tcr' a creation time (in inferencecycles)
            'toc' an occurrence time (in inference cycles)
            'Ca' syntactic complexity (the number of subterms in the associated term)
            'E' an evidential set.
        """
        next_stamp_id = 0

        def __init__(self):
            self.id = self.get_next_stamp_id()
            self.creation_time = Global.current_cycle_number  # when was this stamp created (in inference cycles)?
            self.occurrence_time = -1  # todo, estimate of when did this event occur (in inference cycles)
            self.syntactic_complexity = -1  # todo, number of subterms
            self.evidential_base = self.EvidentialBase(self.id)
            self.interacted_sentences = []  # list of sentence this sentence has already interacted with

        def mutually_add_to_interacted_sentences(self, sentence):
            self.interacted_sentences.append(sentence)
            if len(self.interacted_sentences) > Config.MAX_INTERACTED_SENTENCES_LENGTH:
                self.interacted_sentences.pop(0)

            sentence.stamp.interacted_sentences.append(sentence)
            if len(sentence.stamp.interacted_sentences) > Config.MAX_INTERACTED_SENTENCES_LENGTH:
                sentence.stamp.interacted_sentences.pop(0)

        @classmethod
        def get_next_stamp_id(cls):
            cls.next_stamp_id = cls.next_stamp_id + 1
            return cls.next_stamp_id - 1

        class EvidentialBase:
            """
                Stores history of how the sentence was derived
            """
            def __init__(self, id):
                self.base = []  # array of integer IDs
                self.base.append(id)  # append this sentence's

            def merge_evidential_base_into_self(self, other_base):
                """
                    Merge other evidential base into self.
                    This function assumes the base to merge does not have evidential overlap with this base
                    #todo figure out good way to store evidential bases such that older evidence is purged on overflow
                """
                for id in other_base.base:
                    self.base.append(id)

                while len(self.base) > Config.MAX_EVIDENTIAL_BASE_LENGTH:
                    self.base.pop(0)

            def has_evidential_overlap(self, other_base):
                """
                    Check does other base has overlapping evidence with self?
                    O(M + N)
                    https://stackoverflow.com/questions/3170055/test-if-lists-share-any-items-in-python
                """
                return not set(self.base).isdisjoint(other_base.base)


class Judgment(Sentence):
    """
        judgment ::= <statement>. %<truth-value>%
    """

    def __init__(self, statement, value):
        assert_statement(statement)
        assert_truth_value(value)
        super().__init__(statement, value, Punctuation.Judgment)

    def __str__(self):
        return self.get_formatted_string()


class Question(Sentence):
    """
        question ::= <statement>? %<truth-value>%
    """

    def __init__(self, statement):
        assert_statement(statement)
        super().__init__(statement, None, Punctuation.Question)

    def __str__(self):
        return self.get_formatted_string()


class Statement:
    """
        statement ::= <subject><copula><predicate>
    """

    def __init__(self, subject, predicate, copula):
        assert_term(subject)
        assert_term(predicate)
        assert_copula(copula)
        self.copula: Copula = copula
        self.term: StatementTerm = StatementTerm(subject, predicate, copula)

    def get_subject_term(self):
        return self.term.get_subject_term()

    def get_predicate_term(self):
        return self.term.get_predicate_term()

    def get_formatted_string(self):
        return self.term.get_formatted_string()


class EvidentialValue:
    """
        <frequency, confidence>
    """

    def __init__(self, frequency, confidence):
        assert (isinstance(frequency, float)), "frequency must be a float"
        assert (isinstance(confidence, float)), "confidence must be a float"
        self.frequency = frequency
        self.confidence = confidence


class DesireValue(EvidentialValue):
    """
        <frequency, confidence>
        For a virtual judgement S |=> D,
        how much the associated statement S implies the overall desired state of NARS, D
    """

    def __init__(self, frequency, confidence):
        super().__init__(frequency=frequency, confidence=confidence)

    def get_formatted_string(self):
        return str(StatementSyntax.TruthValMarker.value) \
               + "{:.2f}".format(self.frequency) \
               + str(StatementSyntax.TruthValDivider.value) \
               + "{:.2f}".format(self.confidence) \
               + str(StatementSyntax.TruthValMarker.value)


class TruthValue(EvidentialValue):
    """
        <frequency, confidence> <tense> <timestamp>
        Describing the evidential basis for the associated statement to be true
    """

    def __init__(self, frequency, confidence, tense=None):
        self.tense = tense
        super().__init__(frequency=frequency, confidence=confidence)

    def get_formatted_string(self):
        tense = ""
        if self.tense is not None:
            tense = self.tense.value + " "
        return tense \
               + str(StatementSyntax.TruthValMarker.value) \
               + "{:.2f}".format(self.frequency) \
               + str(StatementSyntax.TruthValDivider.value) \
               + "{:.2f}".format(self.confidence) \
               + str(StatementSyntax.TruthValMarker.value)


class Term:
    """
        Base class for all terms.
    """

    def __init__(self, term_string):
        assert (isinstance(term_string, str)), term_string + " must be a str"
        self.string = term_string
        self.syntactic_complexity = self.calculate_syntactic_complexity()

    def get_formatted_string(self):
        return self.string

    def __eq__(self, other):
        """
            Terms are equal if their strings are the same
        """
        if isinstance(other, StatementTerm):
            return str(self) == str(other) or str(self) == other.get_reverse_term_string()
        elif isinstance(self, StatementTerm):
            return str(self) == str(other) or self.get_reverse_term_string() == str(other)
        elif isinstance(other, Term):  # neither is a Statement term
            return str(self) == str(other)
        return False

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return self.get_formatted_string()

    def calculate_syntactic_complexity():
        assert False, "Complexity not defined for Term base class"

    def contains_variable(self):
        return VariableTerm.VARIABLE_SYM in str(self) \
                or VariableTerm.QUERY_SYM in str(self)

    @classmethod
    def get_term_from_string(cls, term_string):
        """
            Determine if it is an atomic term (e.g. "A") or a statement/compound term (e.g. (&&,A,B,..) or (A --> B))
            or variable term and creates the corresponding Term.

            :param term_string - String from which to construct the term
            :returns Term constructed using the string
        """
        is_set_term = TermConnector.is_set_bracket_start(term_string[0])
        if term_string[0] == StatementSyntax.Start.value:
            """
                Compound or Statement Term
            """
            assert (term_string[-1] == StatementSyntax.End.value), "Compound/Statement term must have ending parenthesis: " + term_string

            copula, copula_idx = get_top_level_copula(term_string)
            if copula is None:
                # compound term
                term = CompoundTerm.from_string(term_string)
            else:
                # statement term
                term = StatementTerm.from_string(term_string)
        elif is_set_term:
            term = CompoundTerm.from_string(term_string)
        elif term_string[0] == VariableTerm.VARIABLE_SYM or term_string[0] == VariableTerm.QUERY_SYM:
            # variable term
            dependency_list_start_idx = term_string.find("(")
            if dependency_list_start_idx == -1:
                variable_name = term_string[1:]
                dependency_list_string = ""
            else:
                variable_name = term_string[1:dependency_list_start_idx]
                dependency_list_string = term_string[term_string.find("(") + 1:term_string.find(")")]

            term = VariableTerm.from_string(variable_name=variable_name,
                                            variable_type_symbol=term_string[0],
                                            dependency_list_string=dependency_list_string)
        else:
            term = AtomicTerm(term_string)

        return term


class VariableTerm(Term):
    class Type(enum.Enum):
        Independent = 1
        Dependent = 2
        Query = 3

    VARIABLE_SYM = "#"
    QUERY_SYM = "?"

    def __init__(self, variable_name: str, variable_type: Type, dependency_list=None):
        """

        :param variable_string: variable name
        :param variable_type: type of variable
        :param dependency_list: array of independent variables this variable depends on
        """
        # todo parse variable terms from input strings
        self.variable_name = variable_name
        self.variable_type = variable_type
        self.variable_symbol = VariableTerm.QUERY_SYM if variable_type == VariableTerm.Type.Query else VariableTerm.VARIABLE_SYM
        self.dependency_list = dependency_list
        super().__init__(self.get_formatted_string())

    def get_formatted_string(self):
        dependency_string = ""
        if self.dependency_list is not None:
            dependency_string = "("
            for dependency in self.dependency_list:
                dependency_string = dependency_string + str(dependency) + ","

            dependency_string = dependency_string[0:-1] + ")"

        return self.variable_symbol + self.variable_name + dependency_string

    @classmethod
    def from_string(cls, variable_name: str, variable_type_symbol: str, dependency_list_string: str):
        # parse dependency list
        dependency_list = None

        if len(dependency_list_string) > 0:
            dependency_list = []

        type = None
        if variable_type_symbol == VariableTerm.QUERY_SYM:
            type = VariableTerm.Type.Query
        elif variable_type_symbol == VariableTerm.VARIABLE_SYM:
            if dependency_list is None:
                type = VariableTerm.Type.Independent
            else:
                type = VariableTerm.Type.Dependent

        assert type is not None, "Error: Variable type symbol invalid"
        return cls(variable_name, type, dependency_list)

    def calculate_syntactic_complexity(self):
        if self.dependency_list is None:
            return 1
        else:
            return 1 + len(self.dependency_list)


class AtomicTerm(Term):
    """
        An atomic term, named by a valid word.
    """

    def __init__(self, term_string):
        """
        Input:
            subterms: array of terms or compound terms

            connector: Connector
        """
        assert (AtomicTerm.is_valid_term(term_string)), term_string + " is not a valid Atomic Term name."
        super().__init__(term_string)

    @classmethod
    def is_valid_term(cls, term_string):
        for char in term_string:
            if char not in valid_term_chars: return False
        return True

    def calculate_syntactic_complexity(self):
        return 1


class CompoundTerm(Term):
    """
        A term that contains multiple atomic subterms connected by a connector (including copula).

        (Connector T1, T2, ..., Tn)
    """

    def __init__(self, subterms: [Term], connector):
        """
        Input:
            subterms: array of immediate subterms

            connector: subterm connector
        """
        self.subterms: [Term] = subterms
        self.connector = connector  # sets are represented by the opening bracket as the connector, { or [
        self.is_set = (self.connector.value == TermConnector.IntensionalSetStart.value) or \
                      (self.connector.value == TermConnector.ExtensionalSetStart.value)
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

        compound_term_string = compound_term_string.replace(" ","")
        subterms = []
        internal_string = compound_term_string[1:-1] # no parentheses () or set brackets [], {}

        # check for intensional/extensional set [a,b], {a,b}
        connector = TermConnector.get_term_connector_from_string(compound_term_string[0])
        if connector is None:
            # otherwise check for regular Term/Statement connectors
            connector = StatementConnector.get_statement_connector_from_string(internal_string[0:2])
            if connector is None:
                connector = TermConnector.get_term_connector_from_string(internal_string[0])
            assert (internal_string[
                        len(
                            connector.value)] == ','), "Connector not followed by comma in CompoundTerm string " + compound_term_string
            internal_string = internal_string[len(connector.value) + 1:]
        else:
            # intensional/extensional set [a,b], {a,b}
            internal_string = internal_string

        assert (connector is not None), "Connector could not be parsed from CompoundTerm string."

        depth = 0
        subterm_string = ""
        for i, c in enumerate(internal_string):
            if c == StatementSyntax.Start.value or TermConnector.is_set_bracket_start(c):
                depth = depth + 1
            elif c == StatementSyntax.End.value or TermConnector.is_set_bracket_end(c):
                depth = depth - 1

            if c == "," and depth == 0:
                subterm = Term.get_term_from_string(subterm_string)
                subterms.append(subterm)
                subterm_string = ""
            else:
                subterm_string = subterm_string + c

        subterm = Term.get_term_from_string(subterm_string)
        subterms.append(subterm)

        return subterms, connector

    def calculate_syntactic_complexity(self):
        """
            Recursively calculate the syntactic complexity of
            the compound term. The connector adds 1 complexity,
            and the subterms syntactic complexities are summed as well.
        """
        count = 1  # the term connector
        for subterm in self.subterms:
            count = count + subterm.calculate_syntactic_complexity()
        return count

    def get_formatted_string(self):
        if self.is_set:
            string = self.connector.value
        else:
            string = self.connector.value + ","

        for subterm in self.subterms:
            string = string + str(subterm) + ","

        string = string[:-1]

        if self.is_set:
            return string + TermConnector.get_set_end_connector_from_set_start_connector(self.connector).value
        else:
            return "(" + string + ")"


class StatementTerm(CompoundTerm):
    """
        A special kind of compound term with a subject, predicate, and copula

        (P --> Q)
    """

    def __init__(self, subject: Term, predicate: Term, copula: Copula):
        assert_term(subject)
        assert_term(predicate)
        assert_copula(copula)
        super().__init__([subject, predicate], copula)
        if copula == Copula.Similarity:
            self.equivalent_term_string = self._get_formatted_string_from_values(predicate, subject)

    @classmethod
    def from_string(cls, term_string):
        """
        :param term_string: string to turn into a Statement Term
        :return: The Statement Term created from the term_string
        """
        subject, predicate, connector, _ = parse_subject_predicate_copula_and_copula_index(term_string)
        return cls(subject, predicate, connector)

    def get_subject_term(self) -> Term:
        return self.subterms[0]

    def get_predicate_term(self) -> Term:
        return self.subterms[1]

    def get_copula_string(self):
        return str(self.connector.value)

    def get_formatted_string(self):
        """
            returns: (Subject copula Predicate)
        """
        return self._get_formatted_string_from_values(self.get_subject_term(), self.get_predicate_term())

    def _get_formatted_string_from_values(self, subject_term, predicate_term):
        return StatementSyntax.Start.value + \
               subject_term.get_formatted_string() + \
               " " + self.get_copula_string() + " " + \
               predicate_term.get_formatted_string() \
               + StatementSyntax.End.value

    def get_reverse_term_string(self):
        if not Copula.is_symmetric(self.connector):
            # no such thing as a reverse term for non-symmetric statements
            return None
        return self.equivalent_term_string


def parse_subject_predicate_copula_and_copula_index(statement_string):
    """
        Parameter: statement_string - String of NAL syntax "(term copula term)"

        Returns: top-level subject term, predicate term, copula, copula index
    """
    statement_string = statement_string.replace(" ","")

    # get copula
    copula, copula_idx = get_top_level_copula(statement_string)
    assert (copula is not None), "Copula not found. Exiting.."

    subject_str = statement_string[1:copula_idx] # get subject string
    predicate_str = statement_string[copula_idx + len(copula.value):len(statement_string) - 1]  # get predicate string

    return Term.get_term_from_string(subject_str), Term.get_term_from_string(predicate_str), copula, copula_idx


def get_top_level_copula(string):
    """
        Searches for top-level copula in the string.

        :returns copula and index if it exists,
        :returns none and -1 otherwise
    """
    copula = None
    copula_idx = -1

    depth = 0
    for i, v in enumerate(string):
        if v == StatementSyntax.Start.value:
            depth = depth + 1
        elif v == StatementSyntax.End.value:
            depth = depth - 1
        elif depth == 1 and i + 3 <= len(string) and Copula.is_string_a_copula(string[i:i + 3]):
            copula, copula_idx = Copula.get_copula_from_string(string[i:i + 3]), i

    return copula, copula_idx


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
