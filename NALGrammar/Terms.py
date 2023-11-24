"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Enforces Narsese grammar that is used throughout the project
"""
import enum
import re

import numpy as np

import Global
import NALSyntax
import Asserts
from NALGrammar import Sentences, Values

"""
Helper Functions
"""

def is_valid_statement(term):
    return isinstance(term, StatementTerm) or \
           (isinstance(term, CompoundTerm) and not term.is_first_order())

def from_string(term_string):
    """
        Determine if it is an atomic term (e.g. "A") or a statement/compound term (e.g. (&&,A,B,..) or (A --> B))
        or variable term and creates the corresponding Term.

        :param term_string - String from which to construct the term
        :returns Term constructed using the string
    """
    term_string = term_string.replace(" ", "")

    assert len(term_string) > 0, "ERROR: Cannot convert empty string to a Term."

    if term_string[0] == NALSyntax.StatementSyntax.Start.value:
        """
            Compound or Statement Term
        """
        assert (term_string[-1] == NALSyntax.StatementSyntax.End.value),\
            "Compound/Statement term must have ending parenthesis: " + term_string

        copula, copula_idx = NALSyntax.Copula.get_top_level_copula(term_string)
        if copula is None:
            # compound term
            term = CompoundTerm.from_string(term_string)
        else:
            term = StatementTerm.from_string(term_string)
    elif NALSyntax.TermConnector.is_set_bracket_start(term_string[0]):
        # set term
        term = CompoundTerm.from_string(term_string)
    elif term_string[0] == VariableTerm.VARIABLE_SYM \
            or term_string[0] == VariableTerm.QUERY_SYM:
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
        term_string = re.sub(",\d+", "", term_string)
        term = AtomicTerm(term_string)

    return term


def simplify(term):
    """
        Simplifies a term and its subterms,
        using NAL Theorems.

        :returns The simplified term
    """
    return term #todo
    simplified_term = term

    if isinstance(term, StatementTerm):
        simplified_term = StatementTerm(subject_term=simplify(term.get_subject_term()),
                                        predicate_term=simplify(term.get_predicate_term()),
                                        copula=term.get_copula(),
                                        interval=term.interval)
    elif isinstance(term, CompoundTerm):
        if term.connector == NALSyntax.TermConnector.Negation and \
                len(term.subterms) == 1 and \
                isinstance(term.subterms[0], CompoundTerm) and \
                term.subterms[0].connector == NALSyntax.TermConnector.Negation:
            # (--,(--,(S --> P)) <====> (S --> P)
            # Double negation theorem. 2 Negations cancel out
            simplified_term = simplify(term.subterms[0].subterms[0])  # get the inner statement
        # elif NALSyntax.TermConnector.is_conjunction(term.connector):
        #         #(&&,A,B..C)
        #         new_subterms = []
        #         new_intervals = []
        #         for i in range(len(term.subterms)):
        #             subterm = simplify(term.subterms[i])
        #             if i < len(term.intervals): new_intervals.append(term.intervals[i])
        #             if isinstance(subterm, CompoundTerm) and subterm.connector == term.connector:
        #                 # inner conjunction
        #                 new_subterms.extend(subterm.subterms)
        #                 new_intervals.extend(subterm.intervals)
        #             else:
        #                 new_subterms.append(subterm)
        #
        #         simplified_term = CompoundTerm(subterms=new_subterms,
        #                             term_connector=term.connector,
        #                                        intervals=new_intervals)
        elif term.connector is NALSyntax.TermConnector.ExtensionalDifference:
            pass
        elif term.connector is NALSyntax.TermConnector.IntensionalDifference:
            pass
        elif term.connector is NALSyntax.TermConnector.ExtensionalImage:
            pass
        elif term.connector is NALSyntax.TermConnector.IntensionalImage:
            pass

    return simplified_term


class Term:
    """
        Base class for all terms.
    """
    term_id = 0
    def __init__(self,
                 term_string):
        assert isinstance(term_string, str), term_string + " must be a str"
        self.string = term_string
        self.syntactic_complexity = 0#self._calculate_syntactic_complexity()

    @classmethod
    def get_next_term_ID(cls):
        cls.term_id += 1
        return cls.term_id

    def get_term_string(self):
        return self.string

    def __eq__(self, other):
        """
            Terms are equal if their strings are the same
        """
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return self.get_term_string()

    def _calculate_syntactic_complexity(self):
        assert False, "Complexity not defined for Term base class"

    def is_op(self):
        return False

    def contains_variable(self):
        return VariableTerm.VARIABLE_SYM in str(self) \
               or VariableTerm.QUERY_SYM in str(self)


class VariableTerm(Term):
    class Type(enum.Enum):
        Independent = 1
        Dependent = 2
        Query = 3

    VARIABLE_SYM = "#"
    QUERY_SYM = "?"

    def __init__(self,
                 variable_name: str,
                 variable_type: Type,
                 dependency_list=None):
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
        super().__init__(self._create_term_string())

    def _create_term_string(self):
        dependency_string = ""
        if self.dependency_list is not None:
            dependency_string = "("
            for dependency in self.dependency_list:
                dependency_string = dependency_string + str(dependency) + NALSyntax.StatementSyntax.TermDivider.value

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

    def _calculate_syntactic_complexity(self):
        if self.syntactic_complexity is not None: return self.syntactic_complexity
        if self.dependency_list is None:
            return 1
        else:
            return 1 + len(self.dependency_list)


class AtomicTerm(Term):
    """
        An atomic term, named by a valid word.
    """

    def __init__(self,
                 term_string):
        """
        Input:
            term_string = name of the term
        """
        assert (AtomicTerm.is_valid_term(term_string)), term_string + " is not a valid Atomic Term name."
        super().__init__(term_string)

    def _calculate_syntactic_complexity(self):
        return 1

    @classmethod
    def is_valid_term(cls, term_string):
        for char in term_string:
            if char not in NALSyntax.valid_term_chars: return False
        return True


class CompoundTerm(Term):
    """
        A term that contains multiple atomic subterms connected by a connector.

        (Connector T1, T2, ..., Tn)
    """

    def __init__(self, subterms: [Term],
                 term_connector: NALSyntax.TermConnector,
                 intervals=None):
        """
        Input:
            subterms: array of immediate subterms

            term_connector: subterm connector (can be first-order or higher-order).
                            sets are represented with the opening bracket as the connector, { or [

            intervals: array of time intervals between statements (only used for sequential conjunction)
        """
        assert term_connector is not None,"ERROR: A compound term needs a term connector."

        self.subterms: [Term] = np.array(subterms)
        self.connector = term_connector
        self.intervals = []

        if len(subterms) > 1:
            # handle intervals for the relevant temporal connectors.
            if term_connector == NALSyntax.TermConnector.SequentialConjunction:
                # (A &/ B ...)
                if intervals is not None and len(intervals) > 0:
                    self.intervals = intervals
                else:
                    # if generic conjunction from input, assume interval of 1
                    # todo accept intervals from input
                    self.intervals = [1] * (len(subterms) - 1)

                #self.string_with_interval = self._create_term_string_with_interval()
            elif term_connector == NALSyntax.TermConnector.ParallelConjunction:
                # (A &| B ...)
                # interval of 0
                self.intervals = [0] * (len(subterms) - 1)

            # decide if we need to maintain the ordering
            if NALSyntax.TermConnector.is_order_invariant(term_connector):
                # order doesn't matter, alphabetize so the system can recognize the same term
                subterms.sort(key=lambda t: str(t))

            # check if it's a set
            is_extensional_set = (term_connector == NALSyntax.TermConnector.ExtensionalSetStart)
            is_intensional_set = (term_connector == NALSyntax.TermConnector.IntensionalSetStart)
            is_set = is_extensional_set or is_intensional_set

            # handle multi-component sets
            if is_set:
                # todo handle multi-component sets better
                singleton_set_subterms = []

                for subterm in subterms:
                    # decompose the set into an intersection of singleton sets
                    singleton_set_subterm = CompoundTerm(subterms=[subterm],
                                                         term_connector=NALSyntax.TermConnector.get_set_end_connector_from_set_start_connector(term_connector))

                    singleton_set_subterms.append(singleton_set_subterm)

                self.subterms = singleton_set_subterms

                # set new term connector as intersection
                if is_extensional_set:
                    self.connector = NALSyntax.TermConnector.IntensionalIntersection
                elif is_intensional_set:
                    self.connector = NALSyntax.TermConnector.ExtensionalIntersection

        # store if this is an operation (meaning all of its components are)
        self.is_operation = True
        for i, subterm in np.ndenumerate(self.subterms):
            self.is_operation = self.is_operation and subterm.is_op()

        Term.__init__(self, term_string=self._create_term_string())

    def is_op(self):
        return self.is_operation

    def contains_op(self):
        for subterm in self.subterms:
            if subterm.is_op():
                return True
        return False

    def contains_positive(self):
        for subterm in self.subterms:
            subterm_concept = Global.Global.NARS.memory.peek_concept(subterm)
            if not subterm.is_op() and subterm_concept.term_contains_positive():
                return True
        return False

    def is_first_order(self):
        return NALSyntax.TermConnector.is_first_order(self.connector)

    def is_intensional_set(self):
        return self.connector == NALSyntax.TermConnector.IntensionalSetStart

    def is_extensional_set(self):
        return self.connector == NALSyntax.TermConnector.ExtensionalSetStart

    def is_set(self):
        return self.is_intensional_set() or self.is_extensional_set()

    def get_term_string_with_interval(self):
        return None #self.string_with_interval

    def _create_term_string_with_interval(self):
        if self.is_set():
            string = self.connector.value
        else:
            string = self.connector.value + NALSyntax.StatementSyntax.TermDivider.value

        for i in range(len(self.subterms)):
            subterm = self.subterms[i]
            string += subterm.get_term_string() + NALSyntax.StatementSyntax.TermDivider.value
            if self.connector == NALSyntax.TermConnector.SequentialConjunction and i < len(self.intervals):
                string = string + str(self.intervals[i]) + NALSyntax.StatementSyntax.TermDivider.value

        string = string[:-1]  # remove the final term divider

        if self.is_set():
            return string + NALSyntax.TermConnector.get_set_end_connector_from_set_start_connector(self.connector).value
        else:
            return NALSyntax.StatementSyntax.Start.value + string + NALSyntax.StatementSyntax.End.value

    def _create_term_string(self):
        if self.is_set():
            string = self.connector.value
        else:
            string = self.connector.value + NALSyntax.StatementSyntax.TermDivider.value

        for i in range(len(self.subterms)):
            subterm = self.subterms[i]
            string = string + subterm.get_term_string() + NALSyntax.StatementSyntax.TermDivider.value

        string = string[:-1]  # remove the final term divider

        if self.is_set():
            return string + NALSyntax.TermConnector.get_set_end_connector_from_set_start_connector(
                self.connector).value
        else:
            return NALSyntax.StatementSyntax.Start.value + string + NALSyntax.StatementSyntax.End.value

    def _calculate_syntactic_complexity(self):
        """
            Recursively calculate the syntactic complexity of
            the compound term. The connector adds 1 complexity,
            and the subterms syntactic complexities are summed as well.
        """
        if self.syntactic_complexity is not None: return self.syntactic_complexity
        count = 0
        if self.connector is not None:
            count = 1  # the term connector
        for i, subterm in np.ndenumerate(self.subterms):
            count = count + subterm._calculate_syntactic_complexity()
        return count

    @classmethod
    def from_string(cls, compound_term_string):
        """
            Create a compound term from a string representing a compound term
        """
        compound_term_string = compound_term_string.replace(" ", "")
        subterms, connector, intervals = cls.parse_toplevel_subterms_and_connector(compound_term_string)
        return cls(subterms, connector, intervals=intervals)

    @classmethod
    def parse_toplevel_subterms_and_connector(cls, compound_term_string):
        """
            Parse out all top-level subterms from a string representing a compound term

            compound_term_string - a string representing a compound term
        """
        compound_term_string = compound_term_string.replace(" ", "")
        subterms = []
        intervals = []
        internal_string = compound_term_string[1:-1]  # string with no outer parentheses () or set brackets [], {}

        # check the first char for intensional/extensional set [a,b], {a,b}
        # also check for array @
        connector = NALSyntax.TermConnector.get_term_connector_from_string(compound_term_string[0])
        if connector is None:
            # otherwise check the first 2 chars for regular Term/Statement connectors
            if internal_string[1] == NALSyntax.StatementSyntax.TermDivider.value:
                connector_string = internal_string[0]  # Term connector
            else:
                connector_string = internal_string[0:2]  # Statement connector
            connector = NALSyntax.TermConnector.get_term_connector_from_string(connector_string)

            assert (internal_string[
                        len(
                            connector.value)] == NALSyntax.StatementSyntax.TermDivider.value), "Connector not followed by comma in CompoundTerm string " + compound_term_string
            internal_string = internal_string[len(connector.value) + 1:]

        assert (connector is not None), "Connector could not be parsed from CompoundTerm string."

        depth = 0
        subterm_string = ""
        for i, c in enumerate(internal_string):
            if c == NALSyntax.StatementSyntax.Start.value or NALSyntax.TermConnector.is_set_bracket_start(c):
                depth += 1
            elif c == NALSyntax.StatementSyntax.End.value or NALSyntax.TermConnector.is_set_bracket_end(c):
                depth -= 1

            if c == NALSyntax.StatementSyntax.TermDivider.value and depth == 0:
                if subterm_string.isdigit():
                    intervals.append(int(subterm_string))
                else:
                    subterm = from_string(subterm_string)
                    subterms.append(subterm)
                subterm_string = ""
            else:
                subterm_string += c

        subterm = from_string(subterm_string)
        subterms.append(subterm)

        return subterms, connector, intervals

    def get_negated_term(self):
        if self.connector == NALSyntax.TermConnector.Negation and len(self.subterms) == 1:
            return self.subterms[0]
        else:
            return CompoundTerm(
                subterms=[self],
                term_connector=NALSyntax.TermConnector.Negation)


class StatementTerm(Term):
    """
        <subject><copula><predicate>

        A special kind of compound term with a subject, predicate, and copula.

        (P --> Q)


    """

    def __init__(self,
                 subject_term: Term,
                 predicate_term,
                 copula,
                 interval=0):
        """
        :param subject_term:
        :param predicate_term:
        :param copula:
        :param interval: If first-order (an event):
                            the number of working cycles, i.e. the interval, before the event, if this event was derived from a compound
                        If higher-order (predictive implication)
                            the number of working cycles, i.e. the interval, between the subject and predicate events
        """
        Asserts.assert_term(subject_term)
        Asserts.assert_term(predicate_term)

        self.connector = None
        self.subterms = [subject_term, predicate_term]
        self.interval = interval

        self.copula = None
        if copula is not None:
            self.copula = copula
            if NALSyntax.Copula.is_symmetric(copula):
                self.subterms.sort(key=lambda t: str(t))  # sort alphabetically

        self.is_operation = self.calculate_is_operation()

        Term.__init__(self, term_string=self._create_term_string())

    @classmethod
    def from_string(cls, statement_string):
        """
            Parameter: statement_string - String of NAL syntax "(term copula term)"

            Returns: top-level subject term, predicate term, copula, copula index
        """
        statement_string = statement_string.replace(" ", "")
        # get copula
        copula, copula_idx = NALSyntax.Copula.get_top_level_copula(statement_string)
        assert (copula is not None), "Copula not found. Exiting.."

        subject_str = statement_string[1:copula_idx]  # get subject string
        predicate_str = statement_string[
                        copula_idx + len(copula.value):len(statement_string) - 1]  # get predicate string

        interval = 0
        if not NALSyntax.Copula.is_first_order(copula):
            last_element = subject_str.split(",")[-1]
            if last_element[0:-1].isdigit():
                interval = int(last_element[0:-1])

        statement_term = StatementTerm(subject_term=from_string(subject_str),
                                       predicate_term=from_string(predicate_str),
                                       copula=copula,
                                       interval=interval)

        return statement_term

    def _calculate_syntactic_complexity(self):
        """
            Recursively calculate the syntactic complexity of
            the compound term. The connector adds 1 complexity,
            and the subterms syntactic complexities are summed as well.
        """
        if self.syntactic_complexity is not None: return self.syntactic_complexity
        count = 1  # the copula
        for subterm in self.subterms:
            count = count + subterm._calculate_syntactic_complexity()

        return count

    def get_subject_term(self):
        return self.subterms[0]

    def get_predicate_term(self):
        return self.subterms[1]

    def get_copula(self):
        return self.copula

    def get_statement_connector(self):
        return self.connector

    def get_copula_string(self):
        return str(self.get_copula().value)

    def get_term_string_with_interval(self):
        return self.string_with_interval

    def _create_term_string_with_interval(self):
        """
            Returns the term's string with intervals.

            returns: (Subject copula Predicate)
        """
        if isinstance(self.get_subject_term(), CompoundTerm) and self.get_subject_term().connector == NALSyntax.TermConnector.SequentialConjunction:
            string = NALSyntax.StatementSyntax.Start.value + \
                     self.get_subject_term().get_term_string_with_interval()
        else:
            string = NALSyntax.StatementSyntax.Start.value + \
                     self.get_subject_term().get_term_string()

        if not self.is_first_order() and self.interval > 0:
            string = string[:-1] + \
                     NALSyntax.StatementSyntax.TermDivider.value + \
                     str(self.interval) + \
                     string[-1]

        string += " " + self.get_copula_string() + " "

        string += self.get_predicate_term().get_term_string() + \
                  NALSyntax.StatementSyntax.End.value

        return string

    def _create_term_string(self):
        """
            Returns the term's string.

            This is very important, because terms are compared for equality using this string.

            returns: (Subject copula Predicate)
        """
        string = NALSyntax.StatementSyntax.Start.value + \
                 self.get_subject_term().get_term_string()

        string += " " + self.get_copula_string() + " "

        string += self.get_predicate_term().get_term_string() + \
                  NALSyntax.StatementSyntax.End.value

        return string

    def contains_op(self):
        contains = self.is_op()
        if not self.is_first_order():
            contains = contains or \
                       self.get_subject_term().contains_op() or \
                       self.get_predicate_term().contains_op()
        return contains

    def is_op(self):
        return self.is_operation

    def calculate_is_operation(self):
        return isinstance(self.get_subject_term(), CompoundTerm) \
               and self.get_subject_term().connector == NALSyntax.TermConnector.Product \
               and self.get_subject_term().subterms[
                   0] == Global.Global.TERM_SELF  # product and first term is self means this is an operation

    def is_first_order(self):
        return NALSyntax.Copula.is_first_order(self.copula)

    def is_symmetric(self):
        return NALSyntax.Copula.is_symmetric(self.copula)

    def is_positive(self):
        term_concept = Global.Global.NARS.memory.peek_concept(self)
        if term_concept is None: return False
        # todo higher order statements?
        return term_concept.is_positive()

    def contains_positive(self):
        # todo higher order?
        return self.is_positive()

    def get_negated_term(self):
        return CompoundTerm(
            subterms=[self],
            term_connector=NALSyntax.TermConnector.Negation)


class SpatialTerm(CompoundTerm):
    """
        Higher-order Compound with a spatial component.
    """

    def __init__(self,
                 spatial_subterms,
                 connector):
        """
            :param spatial_subterms: a spatial multi-dimensional array of first-order StatementTerms (or their negations).

            todo: support more than 2D
        """
        self.dimensions = spatial_subterms.shape
        self.center = None
        self.of_spatial_terms = isinstance(spatial_subterms.flat[0], SpatialTerm) # flat does not copy the array
        assert len(self.dimensions) == 2,"ERROR: Array Term only supports 2D arrays"
        CompoundTerm.__init__(self,
                              subterms=spatial_subterms,
                              term_connector=connector)
        # self.subterms = None

    def _create_term_string(self):
        """

        :return:
        """
        string = ''
        for indices, element_term in np.ndenumerate(self.subterms):
            string += str(indices[0]) + str(element_term) + str(indices[1]) + '_'

        return NALSyntax.StatementSyntax.Start.value \
                + self.connector.value \
                + string \
                + NALSyntax.StatementSyntax.End.value

   # def img_from_term(self):


    # @classmethod
    # def from_string(cls,string):
    #     # TODO
    #     dimension_split_idx_start = string.find(cls.ARRAY_CARTESIAN_PRODUCT)
    #     dimension_split_idx_end = string.rfind(cls.ARRAY_CARTESIAN_PRODUCT)
    #     y_length, x_length = string[0:dimension_split_idx_start], string[dimension_split_idx_start+1:dimension_split_idx_end]
    #
    #     def parse_spatial_subterms_from_string(*indices):
    #         row, col = tuple([int(var) for var in indices])
    #         element_char = string[dimension_split_idx_end + 1 + x_length * row + col]
    #
    #         subject_name = str(row) + "_" + str(col)
    #         subject_term = AtomicTerm(term_string=subject_name)
    #         positive_statement = StatementTerm(subject_term=subject_term,
    #                                                    predicate_term=predicate_term,
    #                                                    copula=NALSyntax.Copula.Inheritance)
    #         if element_char == cls.ARRAY_POSITIVE_ELEMENT:
    #             element = positive_statement
    #         elif element_char == cls.ARRAY_NEGATIVE_ELEMENT:
    #             element = NALGrammar.Terms.CompoundTerm([positive_statement],
    #                                                       term_connector=NALSyntax.TermConnector.Negation)
    #         else:
    #             assert False,"ERROR: Invalid character in Array string"
    #
    #         if isinstance(element_term, StatementTerm):
    #             string += "P"
    #         elif isinstance(element_term, CompoundTerm) \
    #                 and element_term.connector == NALSyntax.TermConnector.Negation:
    #             string += "N"
    #         return NALInferenceRules.TruthValueFunctions.Expectation(f, c)
    #
    #     func_vectorized = np.vectorize(parse_spatial_subterms_from_string)
    #     expectation_array = np.fromfunction(function=func_vectorized, shape=(y_length, x_length))


