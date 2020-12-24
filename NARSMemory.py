from NALGrammar import *
from NARSDataStructures import Bag

class Memory:
    def __init__(self):
        self.concepts = Bag(item_type=Concept)

    def process_judgment(self, sentence):
        assert_sentence(sentence)
        subject = sentence.statement.subjectPredicate.subject
        predicate = sentence.statement.subjectPredicate.predicate

        self.conceptualize(subject)
        self.conceptualize(predicate)
        self.conceptualize(sentence.statement.term)
        self.add_new_termlink_from_sentence(sentence)

    def conceptualize(self, term):
        assert_term(term)
        c = Concept(term)
        self.concepts.put(c)

    def forget(self, term):
        assert_term(term)
        if term in self.concepts:
            self.concepts.pop(term)

    def add_new_termlink_from_sentence(self, sentence):
        subject_term = sentence.statement.subjectPredicate.subject
        predicate_term = sentence.statement.subjectPredicate.predicate

        subject_concept = self.get_concept_from_term(subject_term)
        predicate_concept = self.get_concept_from_term(predicate_term)

        edge = Edge(subject_concept, predicate_concept, sentence.statement.copula, sentence.truthValue)
        subject_concept.add_outgoing_termlink(edge)
        predicate_concept.add_incoming_termlink(edge)

    def get_concept_from_term(self, term):
        assert_term(term)
        return Concept(term)


class Concept:
    def __init__(self, term):
        assert_term(term)
        self.term = term
        self.incomingEdges = {}
        self.outgoingEdges = {}

    def add_incoming_termlink(self, edge):
        assert_edge(edge)
        # this concept is the predicate
        subject = edge.subject
        if subject in self.incomingEdges:
            self.incomingEdges[subject].append(edge)
        else:
            self.incomingEdges[subject] = [edge]

    def remove_incoming_termlink(self, edge):
        assert_edge(edge)
        # this concept is the predicate
        subject = edge.subject
        if subject in self.incomingEdges:
            self.incomingEdges[subject].remove(edge)

    def add_outgoing_termlink(self, edge):
        assert_edge(edge)
        # this concept is the subject
        predicate = edge.predicate
        if predicate in self.outgoingEdges:
            self.incomingEdges[predicate].append(edge)
        else:
            self.incomingEdges[predicate] = [edge]

    def remove_outgoing_termlink(self, edge):
        assert_edge(edge)
        # this concept is the predicate
        predicate = edge.predicate
        if predicate in self.outgoingEdges:
            self.incomingEdges[predicate].remove(edge)

    def get_formatted_string(self):
        return self.term.get_formatted_string()

    def __str__(self):
        return self.term.get_formatted_string()

    def __eq__(self, other):
        return self.term.get_formatted_string() == other.term.get_formatted_string()

    def __hash__(self):
        return hash(self.term.get_formatted_string())


class Edge:
    def __init__(self, subject, predicate, copula, truth_value):
        assert_concept(subject)
        assert_concept(predicate)
        self.subject = subject
        self.predicate = predicate
        self.copula = copula
        self.truthValue = truth_value


def assert_concept(c):
    assert (isinstance(c, Concept)), str(c) + " must be a Concept"

def assert_edge(edge):
    assert (isinstance(edge, Edge)), str(edge) + " must be an Edge"
