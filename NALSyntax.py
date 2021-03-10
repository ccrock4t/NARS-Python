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


class Tense(enum.Enum):
    Future = ":/:"
    Past = ":\:"
    Present = ":|:"

    @classmethod
    def get_tense_from_string(cls, value):
        for tense in cls:
            if value == tense.value:
                return tense

        return None


class StatementConnector(enum.Enum):
    # NAL-5
    Negation = "--"
    Conjunction = "&&"
    Disjunction = "||"
    SequentialConjunction = "&/"
    ParallelConjunction = "&|"

    @classmethod
    def is_string_a_statement_connector(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_statement_connector_from_string(cls, value):
        if not StatementConnector.is_string_a_statement_connector(value):
            return None

        for connector in cls:
            if value == connector.value:
                return connector

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
    IntensionalImage = r"\\"
    ImagePlaceHolder = "_"

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
    def get_set_end_connector_from_set_start_connector(cls, start_connector):
        if start_connector == TermConnector.ExtensionalSetStart: return TermConnector.ExtensionalSetEnd
        if start_connector == TermConnector.IntensionalSetStart: return TermConnector.IntensionalSetEnd
        return None


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


class Punctuation(enum.Enum):
    Judgment = "."
    Question = "?"  # on truth-value
    Goal = "!"
    Quest = "@"  # on desire-value

    @classmethod
    def is_punctuation(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_punctuation(cls, value):
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
    'a': 1, 'b': 1, 'c': 1, 'd': 1, 'e': 1, 'f': 1, 'g': 1, 'h': 1, 'i': 1, 'j': 1, 'k': 1, 'l': 1, 'm': 1,
    'n': 1, 'o': 1, 'p': 1, 'q': 1, 'r': 1, 's': 1, 't': 1, 'u': 1, 'v': 1, 'w': 1, 'x': 1, 'y': 1, 'z': 1,
    'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1, 'F': 1, 'G': 1, 'H': 1, 'I': 1, 'J': 1, 'J': 1, 'L': 1, 'M': 1,
    'N': 1, 'O': 1, 'P': 1, 'Q': 1, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 1, 'W': 1, 'X': 1, 'Y': 1, 'Z': 1
}
