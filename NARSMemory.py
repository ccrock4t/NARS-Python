import random

import Config
import NALGrammar
import NALSyntax
import NARSDataStructures

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Defines NARS internal memory
"""


class Memory:
    """
        NARS Memory
    """
    next_stamp_id = 0

    def __init__(self):
        self.concepts_bag = NARSDataStructures.Bag(item_type=Concept,capacity=Config.MEMORY_CONCEPT_CAPACITY)
        self.current_cycle_number = 0

    def __len__(self):
        return self.get_number_of_concepts()

    def get_concept(self):
        """
            Probabilistically peek the concepts
        """
        return self.concepts_bag.peek()

    def get_number_of_concepts(self):
        """
            Get the number of concepts that exist in memory
        """
        return self.concepts_bag.count

    def conceptualize_term(self, term):
        """
            Create a new concept from a term and add it to the bag

            :param term: The term naming the concept to create
            :returns New Concept created from the term
        """
        NALGrammar.assert_term(term)
        concept_key = NARSDataStructures.ItemContainer.Item.get_key_from_object(term)
        assert (self.concepts_bag.peek(concept_key) is None), "Cannot create new concept. Concept already exists."
        # create new concept
        new_concept = Concept(term)

        # put into data structure
        purged_item = self.concepts_bag.put_new(new_concept)

        if purged_item is not None:
            purged_concept_key = NARSDataStructures.ItemContainer.Item.get_key_from_object(purged_item.object)

        return new_concept

    def peek_concept(self, term):
        """
              Peek the concept from memory using its term,
              AND create it if it doesn't exist.
              Also recursively creates all sub-term concepts if they do not exist.

              If it's an `open` variable term, the concept is not created, though if it has sub-terms
               those concepts will be created.

              :param term: The term naming the concept to peek
              :return Concept named by the term
          """
        if isinstance(term, NALGrammar.VariableTerm): return None #todo created concepts for closed variable terms
        concept_key = NARSDataStructures.ItemContainer.Item.get_key_from_object(term)
        concept_item: NARSDataStructures.ItemContainer.Item = self.concepts_bag.peek(concept_key)
        if concept_item is not None:
            return concept_item.object  # return if it already exists

        # it doesn't exist
        # it must be created along with its sub-concepts if necessary
        if not term.contains_variable():
            concept = self.conceptualize_term(term)

        if isinstance(term, NALGrammar.CompoundTerm):
            for subterm in term.subterms:
                # get/create subterm concepts
                subconcept = self.peek_concept(subterm)

                if concept is not None and isinstance(term, NALGrammar.StatementTerm):
                    # do term linking with subterms
                    concept.set_term_link(subconcept)

        return concept

    def get_semantically_related_concept(self, concept):
        """
            Get a concept (named by a Statement Term) that is semantically related to the given concept by a term.
            This can return a belief from the input concept, which can be used in Revision.

            :param concept - Statement-Term Concept for which to find a semantically related Statement-Term concept

            :return Statement-Term Concept semantically related to param: `concept`; None if couldn't find any such belief
        """
        related_concept = None

        if isinstance(concept.term, NALGrammar.StatementTerm):
            subject_term = concept.term.get_subject_term()
            predicate_term = concept.term.get_predicate_term()

            concept_item_related_to_subject = self.peek_concept(subject_term).term_links.peek()
            concept_item_related_to_predicate = self.peek_concept(predicate_term).term_links.peek()

            if concept_item_related_to_subject is not None and \
                    concept_item_related_to_predicate is None: # none from predicate
                related_concept = concept_item_related_to_subject.object
            elif concept_item_related_to_subject is None \
                    and concept_item_related_to_predicate is not None: # none from subject
                related_concept = concept_item_related_to_predicate.object
            elif concept_item_related_to_subject is not None \
                    and concept_item_related_to_predicate is not None:  # one from both
                rand = random.random()
                if rand < 0.5:
                    related_concept = concept_item_related_to_subject.object
                elif rand >= 0.5:
                    related_concept = concept_item_related_to_predicate.object
        else:
            # Non-statement concept
            related_concept_item = self.peek_concept(concept.term).term_links.peek()
            if related_concept_item is None:
                related_concept = None
            else:
                related_concept = related_concept_item.object

        return related_concept

    def get_next_stamp_id(self) -> int:
        """
            :return: next available Stamp ID
        """
        self.next_stamp_id += 1
        return self.next_stamp_id - 1


class Concept:
    """
        NARS Concept
    """
    def __init__(self, term):
        NALGrammar.assert_term(term)
        self.term = term  # concept's unique term
        self.term_links = NARSDataStructures.Bag(item_type=Concept)  # Bag of related concepts (related by term)
        self.belief_table = NARSDataStructures.Table(NALGrammar.Judgment) # todo maybe use Bag(NALGrammar.Sentence)
        self.desire_table = NARSDataStructures.Table(NALGrammar.Goal)

    def __str__(self):
        return self.get_formatted_string()

    def __eq__(self, other):
        return self.get_formatted_string() == other.get_formatted_string()

    def set_term_link(self, concept):
        """
            Set a bidirectional term link between 2 concepts, by placing the concept into
            the term links bag.
            Does nothing if the link already exists
        """
        assert_concept(concept)
        if concept in self.term_links: return  # already linked
        self.term_links.put_new(concept)
        concept.term_links.put_new(self)

    def remove_term_link(self, concept):
        """
            Remove a bidirectional term link between this concept and another concept
            todo: use this somewhere
        """
        assert_concept(concept)
        assert (concept in self.term_links), concept + "must be in term links."
        self.term_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(concept))
        concept.term_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(self))

    def get_formatted_string(self):
        """
            A concept is named by its term
        """
        return self.term.get_formatted_string()


# Asserts
def assert_concept(c):
    assert (isinstance(c, Concept)), str(c) + " must be a Concept"
