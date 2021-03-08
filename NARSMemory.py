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

    def conceptualize_term(self, term):
        """
            If term doesn't name existing concept, create a new concept from a term and add it to the bag
            If term does name existing concept, return the concept

            Returns: Concept
        """
        assert_term(term)
        assert(self.get_concept(term) is None), "Cannot create new concept. Concept already exists."
        # create new concept
        concept = Concept(term)
        self.concepts_bag.put_new_item(concept)
        return concept

    def get_concept(self, term):
        """
            Get a concept from memory using its term
        """
        concept_item = self.concepts_bag.peek(hash(str(term)))
        if concept_item is None:
            return None
        return concept_item.object

    def forget(self, term):
        assert_term(term)


class Concept:
    """
        NARS Concept
    """
    def __init__(self, term):
        assert_term(term)
        self.term = term # concept's unique ID
        self.term_links = Bag(item_type=Concept) # Bag of related concepts (related by term)
        self.task_links = Bag(item_type=Task) # Bag of related tasks
        self.belief_table = Table(Punctuation.Judgment)
        self.desire_table = Table(Punctuation.Goal)

    def set_term_link(self, concept):
        """
            Set a bidirectional term link between 2 concepts. Does nothing if the link already exists
        """
        assert_concept(concept)
        if concept in self.term_links: return # already linked
        self.term_links.put_new_item(concept)
        concept.term_links.put_new_item(self)

    def remove_term_link(self, concept):
        """
            Remove a bidirectional term link between this concept and another concept
            todo: use this somewhere
        """
        assert_concept(concept)
        assert(concept.term in self.term_links), concept.term + "must be in term links."
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
        assert(task in self.task_links), task + "must be in task links."
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