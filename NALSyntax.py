import enum


class StatementSyntax(enum.Enum):
    # Primary copula
    Start = "<"
    End = ">"
    TruthValMarker = "%"
    TruthValDivider = ";"


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
    RetrospectiveImplication = "=\>"
    ConcurrentImplication = "=|>"
    PredictiveEquivalence = "</>"
    ConcurrentEquivalence = "<|>"

    @classmethod
    def is_copula(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def get_copula(cls, value):
        if not Copula.is_copula(value):
            return None

        for copula in cls:
            if value == copula.value:
                return copula

        return None

class Tense(enum.Enum):
    Future = ":/:"
    Past = ":\:"
    Present = ":|:"


class TermConnectors(enum.Enum):
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


class Punctuation(enum.Enum):
    Judgment = "."
    Question = "?"  # on truth-value
    Goal = "!"
    Quest = "!"  # on desire-value

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