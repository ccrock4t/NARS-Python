import enum

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Defines the syntax to be used for Narsese
"""


class StatementSyntax(enum.Enum):
    Start = "("
    End = ")"
    TruthValMarker = "%"
    TruthValDivider = ";"
    TermDivider = ","

    ArrayElementIndexStart = "["
    ArrayElementIndexEnd = "]"


class Tense(enum.Enum):
    Future = ":/:"
    Past = ":\:"
    Present = ":|:"
    Eternal = None

    @classmethod
    def get_tense_from_string(cls, value):
        for tense in cls:
            if value == tense.value:
                return tense

        return None


class TermConnector(enum.Enum):
    # NAL-2
    ExtensionalSetStart = "{"
    ExtensionalSetEnd = "}"
    IntensionalSetStart = "["
    IntensionalSetEnd = "]"

    # NAL-3
    ExtensionalIntersection = "&"
    IntensionalIntersection = "|"
    ExtensionalDifference = "-"
    IntensionalDifference = "~"

    # NAL-4
    Product = "*"
    ExtensionalImage = "/"
    IntensionalImage = "\\"
    ImagePlaceHolder = "_"

    # NAL-5
    Negation = "--"
    Conjunction = "&&"
    Disjunction = "||"
    SequentialConjunction = "&/"
    ParallelConjunction = "&|"

    Array = "@"

    @classmethod
    def is_string_a_term_connector(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_term_connector_from_string(cls, value):
        if not TermConnector.is_string_a_term_connector(value):
            return None

        for connector in cls:
            if value == connector.value:
                return connector

        return None

    @classmethod
    def is_first_order(cls, connector):
        """
            First order connectors are Term Connectors
            Higher order connectors are Statement Connectors
        """
        return not (connector is cls.Negation or
                    connector is cls.Conjunction or
                    connector is cls.Disjunction or
                    connector is cls.SequentialConjunction or
                    connector is cls.ParallelConjunction)

    @classmethod
    def is_order_invariant(cls, connector):
        return (connector is cls.ExtensionalIntersection or
                connector is cls.IntensionalIntersection or
                connector is cls.ExtensionalSetStart or
                connector is cls.IntensionalSetStart or
                connector is cls.Negation or
                connector is cls.Conjunction or
                connector is cls.Disjunction)

    @classmethod
    def is_conjunction(cls, connector):
        return (connector is cls.Conjunction or
                connector is cls.SequentialConjunction or
                connector is cls.ParallelConjunction)


    @classmethod
    def get_set_end_connector_from_set_start_connector(cls, start_connector):
        if start_connector == TermConnector.ExtensionalSetStart: return TermConnector.ExtensionalSetEnd
        if start_connector == TermConnector.IntensionalSetStart: return TermConnector.IntensionalSetEnd
        return None

    @classmethod
    def is_set_bracket_start(cls, bracket):
        """
        Returns true if character is a starting bracket for a set
        :param bracket:
        :return:
        """
        return (bracket == TermConnector.IntensionalSetStart.value) or (
                bracket == TermConnector.ExtensionalSetStart.value)

    @classmethod
    def is_set_bracket_end(cls, bracket):
        """
        Returns true if character is an ending bracket for a set
        :param bracket:
        :return:
        """
        return (bracket == TermConnector.IntensionalSetEnd.value) or (
                bracket == TermConnector.ExtensionalSetEnd.value)


class Copula(enum.Enum):
    # Primary copula
    Inheritance = "-->"
    Similarity = "<->"
    Implication = "==>"
    Equivalence = "<=>"

    # Secondary copula
    Instance = "{--"
    Property = "--]"
    InstanceProperty = "{-]"
    PredictiveImplication = "=/>"
    RetrospectiveImplication = r"=\>"
    ConcurrentImplication = "=|>"
    PredictiveEquivalence = "</>"
    ConcurrentEquivalence = "<|>"

    @classmethod
    def is_first_order(cls, copula):
        return copula is cls.Inheritance \
               or copula is cls.Similarity \
               or copula is cls.Instance \
               or copula is cls.Property \
               or copula is cls.InstanceProperty

    @classmethod
    def is_symmetric(cls, copula):
        return copula == cls.Similarity \
               or copula == cls.Equivalence \
               or copula == cls.PredictiveEquivalence \
               or copula == cls.ConcurrentEquivalence

    @classmethod
    def is_string_a_copula(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_copula_from_string(cls, value):
        if not Copula.is_string_a_copula(value):
            return None

        for copula in cls:
            if value == copula.value:
                return copula

        return None

    @classmethod
    def contains_copula(cls, string):
        for copula in cls:
            if copula.value in string:
                return True
        return False


class Punctuation(enum.Enum):
    Judgment = "."
    Question = "?"  # on truth-value
    Goal = "!"
    Quest = "@"  # on desire-value

    @classmethod
    def is_punctuation(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_punctuation_from_string(cls, value):
        if not Punctuation.is_punctuation(value):
            return None

        for punctuation in cls:
            if value == punctuation.value:
                return punctuation

        return None


"""
List of valid characters that can be used in a term.
"""
valid_term_chars = {
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'J', 'L', 'M',
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "_", "^"
}
