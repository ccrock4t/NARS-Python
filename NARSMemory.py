from NALGrammar import *
from Control_Mechanism import *

class Memory:
    def __init__(self, game):
        self.game = game
        self.concepts = {}

    def add_sentence_to_memory(self, sentence):
        assert_sentence(sentence)
        subject = sentence.statement.subjectPredicate.subject
        predicate = sentence.statement.subjectPredicate.predicate

        self.conceptualize(subject)
        self.conceptualize(predicate)
        self.conceptualize(sentence.statement.term)
        self.add_new_edge_from_sentence(sentence)

    def conceptualize(self, term):
        global game
        assert_term(term)
        if term not in self.concepts:
            c = Concept(term)
            self.concepts[term] = c
            self.game.draw_new_concept()

    def forget(self, term):
        assert_term(term)
        if term in self.concepts:
            self.concepts.pop(term)

    def add_new_edge_from_sentence(self, sentence):
        subject_term = sentence.statement.subjectPredicate.subject
        predicate_term = sentence.statement.subjectPredicate.predicate

        subject_concept = self.get_concept_from_term(subject_term)
        predicate_concept = self.get_concept_from_term(predicate_term)

        edge = Edge(subject_concept, predicate_concept, sentence.statement.copula, sentence.truthValue)
        subject_concept.add_outgoing_edge(edge)
        predicate_concept.add_incoming_edge(edge)

    def get_concept_from_term(self, term):
        assert_term(term)
        if term in self.concepts:
            return self.concepts[term]


class Concept:
    def __init__(self, term):
        self.term = term
        self.incomingEdges = {}
        self.outgoingEdges = {}

    def add_incoming_edge(self, edge):
        assert_edge(edge)
        # this concept is the predicate
        subject = edge.subject
        if subject in self.incomingEdges:
            self.incomingEdges[subject].append(edge)
        else:
            self.incomingEdges[subject] = [edge]

    def remove_incoming_edge(self, edge):
        assert_edge(edge)
        # this concept is the predicate
        subject = edge.subject
        if subject in self.incomingEdges:
            self.incomingEdges[subject].remove(edge)

    def add_outgoing_edge(self, edge):
        assert_edge(edge)
        # this concept is the subject
        predicate = edge.predicate
        if predicate in self.outgoingEdges:
            self.incomingEdges[predicate].append(edge)
        else:
            self.incomingEdges[predicate] = [edge]

    def remove_outgoing_edge(self, edge):
        assert_edge(edge)
        # this concept is the predicate
        predicate = edge.predicate
        if predicate in self.outgoingEdges:
            self.incomingEdges[predicate].remove(edge)

    def __str__(self):
        return str(self.term)


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
