from random import random

import NALGrammar
from NALGrammar import *
from NARSDataStructures import Bag, assert_task, Table, Task

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Defines NARS internal memory
"""


class Memory:
    """
        NARS Memory
    """

    def __init__(self):
        self.concepts_bag = Bag(item_type=Concept)

    def get_number_of_concepts(self):
        """
            Get the number of concepts that exist in memory
        """
        return self.concepts_bag.count

    def conceptualize_term(self, term: Term):
        """
            Create a new concept from a term and add it to the bag

            :param term: The term naming the concept to create
            :returns New Concept created from the term
        """
        assert_term(term)
        assert (self.concepts_bag.peek(hash(term)) is None), "Cannot create new concept. Concept already exists."
        # create new concept
        concept = Concept(term)
        self.concepts_bag.put_new_item(concept)
        return concept

    def peek_concept(self, term: Term):
        """
              Peek the concept from memory using its term,
              and create it if it doesn't exist.
              Also recursively creates all sub-term concepts if they do not exist.

              :param term: The term naming the concept to peek
              :return Concept named by the term
          """
        concept_item = self.concepts_bag.peek(hash(term))
        if concept_item is not None: return concept_item.object  # return if got concept
        # concept not found
        if isinstance(term, StatementTerm) and term.connector == Copula.Similarity:
            #if its a similarity statement term S<->P, check for equivalent Concept P<->S
            concept_item = self.concepts_bag.peek(hash(term.get_equivalent_term_string()))
            if concept_item is not None: return concept_item.object  # return if got concept

        # it must be created, and potentially its sub-concepts
        concept = self.conceptualize_term(term)
        if isinstance(term, NALGrammar.CompoundTerm):
            for subterm in term.subterms:
                # get/create subterm concepts
                subconcept = self.peek_concept(subterm)

                if isinstance(term, NALGrammar.StatementTerm):
                    # do term linking with subterms
                    concept.set_term_link(subconcept)

        return concept

    def get_semantically_related_concept(self, concept):
        """
            Get a belief (named by a Statement Term) that is semantically related to the given concept by a term.
            This can return a belief from the input concept, which can be used in Revision.

            Returns None if couldn't find such a belief
        """
        related_concept = None

        if isinstance(concept.term, StatementTerm):
            subject_term = concept.term.get_subject_term()
            predicate_term = concept.term.get_predicate_term()

            related_concept_from_subject = self.peek_concept(subject_term).term_links.peek().object
            related_concept_from_predicate = self.peek_concept(predicate_term).term_links.peek().object

            if related_concept_from_subject is not None and related_concept_from_predicate is None and related_concept_from_subject is not concept:  # none from subject
                related_concept = related_concept_from_subject
            elif related_concept_from_subject is None and related_concept_from_predicate is not None and related_concept_from_predicate is not concept:  # none from predicate
                related_concept = related_concept_from_predicate
            elif related_concept_from_subject is not None and related_concept_from_predicate is not None:  # one from both
                rand = random()
                if rand < 0.5:
                    related_concept = related_concept_from_subject
                elif rand >= 0.5:
                    related_concept = related_concept_from_predicate

        return related_concept

    def forget(self, term):
        assert_term(term)


class Concept:
    """
        NARS Concept
    """

    def __init__(self, term):
        assert_term(term)
        self.term = term  # concept's unique ID
        self.term_links = Bag(item_type=Concept)  # Bag of related concepts (related by term)
        self.task_links = Bag(item_type=Task)  # Bag of related tasks
        self.belief_table = Table(Punctuation.Judgment)
        self.desire_table = Table(Punctuation.Goal)

    def set_term_link(self, concept):
        """
            Set a bidirectional term link between 2 concepts. Does nothing if the link already exists
        """
        assert_concept(concept)
        if concept in self.term_links: return  # already linked
        self.term_links.put_new_item(concept)
        concept.term_links.put_new_item(self)

    def remove_term_link(self, concept):
        """
            Remove a bidirectional term link between this concept and another concept
            todo: use this somewhere
        """
        assert_concept(concept)
        assert (concept.term in self.term_links), concept.term + "must be in term links."
        self.term_links.take(object=concept.term)
        concept.term_links.take(object=self.term)

    def set_task_link(self, task):
        """
            Add a task link if it doesn't exist, linking this concept to a task
        """
        assert_task(task)
        if task in self.task_links:
            return
        self.task_links.put_new_item(task)

    def remove_task_link(self, task):
        """
            Remove a task link
        """
        assert_task(task)
        assert (task in self.task_links), task + "must be in task links."
        self.task_links.pop(task)

    def get_formatted_string(self):
        return self.term.get_formatted_string()

    def __str__(self):
        return self.term.get_formatted_string()

    def __eq__(self, other):
        return self.term.get_formatted_string() == other.term.get_formatted_string()

    def __hash__(self):
        """
            A concept is named by its term
        """
        return hash(str(self.term))


# Asserts
def assert_concept(c):
    assert (isinstance(c, Concept)), str(c) + " must be a Concept"
