import random

import Asserts
import Config
import NALGrammar
import NALSyntax
import NARSDataStructures.Bag
import NARSDataStructures.Other
import NARSDataStructures.ItemContainers
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
    next_percept_id = 0

    def __init__(self):
        self.concepts_bag = NARSDataStructures.Bag.Bag(item_type=Concept,capacity=Config.MEMORY_CONCEPT_CAPACITY)
        self.current_cycle_number = 0

    def __len__(self):
        return self.get_number_of_concepts()

    def get_random_concept(self):
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
            :returns New Concept item created from the term
        """
        Asserts.assert_term(term)
        concept_key = NARSDataStructures.ItemContainers.Item.get_key_from_object(term)
        assert (self.concepts_bag.peek(concept_key) is None), "Cannot create new concept. Concept already exists."
        # create new concept
        new_concept = Concept(term)

        # put into data structure
        purged_item = self.concepts_bag.put_new(new_concept)

        if purged_item is not None:
            purged_concept_key = NARSDataStructures.ItemContainers.Item.get_key_from_object(purged_item.object)

        return self.concepts_bag.peek(concept_key)

    def peek_concept_item(self, term):
        """
              Peek the concept from memory using its term,
              AND create it if it doesn't exist.
              Also recursively creates all sub-term concepts if they do not exist.

              If it's an `open` variable term, the concept is not created, though if it has sub-terms
               those concepts will be created.

              :param term: The term naming the concept to peek
              :return Concept named by the term
          """
        if isinstance(term, NALGrammar.Terms.VariableTerm): return None #todo created concepts for closed variable terms
        if isinstance(term,NALGrammar.Terms.ArrayTermElementTerm) \
                or (isinstance(term,NALGrammar.Terms.StatementTerm) \
                and isinstance(term.get_subject_term(),NALGrammar.Terms.CompoundTerm)
                and isinstance(term.get_subject_term().subterms[0], NALGrammar.Terms.ArrayTermElementTerm)): return None  # todo created concepts for closed variable terms

        # try to find the existing concept
        concept_key = NARSDataStructures.ItemContainers.Item.get_key_from_object(term)
        concept_item: NARSDataStructures.ItemContainers.Item = self.concepts_bag.peek(concept_key)
        if concept_item is not None:
            return concept_item  # return if it already exists

        # it doesn't exist
        # it must be created along with its sub-concepts if necessary
        if not isinstance(term, NALGrammar.Terms.VariableTerm):
            concept_item = self.conceptualize_term(term)

            if isinstance(term, NALGrammar.Terms.CompoundTerm):
                for subterm in term.subterms:
                    # get/create subterm concepts
                    if not isinstance(subterm, NALGrammar.Terms.VariableTerm) \
                        and not isinstance(subterm, NALGrammar.Terms.ArrayTermElementTerm): # don't create concepts for variables or array elements
                        subconcept = self.peek_concept_item(subterm).object
                        # do term linking with subterms
                        concept_item.object.set_term_link(subconcept)

            if isinstance(term, NALGrammar.Terms.StatementTerm) and \
                    term.get_copula() is not None and\
                    not NALSyntax.Copula.is_first_order(term.get_copula()):
                # implication statement
                subject_concept = self.peek_concept_item(term.get_subject_term()).object
                predicate_concept = self.peek_concept_item(term.get_predicate_term()).object

                # do prediction/explanation linking with subterms
                subject_concept.set_prediction_link(predicate_concept)
                predicate_concept.set_explanation_link(subject_concept)

        return concept_item

    def get_semantically_related_concepts(self, statement_concept):
        """
            Get concepts (named by a Statement Term) that are semantically related to the given concept.

            Using term-links, returns a concept with the same copula order; one for the subject and one for the predicate.

            For a first-order statement, will also try to return higher-order concepts based on implication links

            :param statement_concept - Statement-Term Concept for which to find a semantically related Statement-Term concept

            :return Statement-Term Concepts semantically related to param: `statement_concept`
        """
        related_concepts = [statement_concept] # a concept is related to itself

        if len(statement_concept.term_links) != 0:
            term_linked_concept = statement_concept.term_links.peek().object

            if isinstance(term_linked_concept.term, NALGrammar.Terms.AtomicTerm):
                # atomic term concept
                related_statement_concept = term_linked_concept.term_links.peek().object # peek additional term links to get another statement term

                related_concepts.append(related_statement_concept)
            else:
                if isinstance(term_linked_concept.term, NALGrammar.Terms.StatementTerm):
                    # the term-linked sentence is a first-order or high-order statement concept
                    # return this statement concept
                    related_concepts.append(term_linked_concept)

                    if not NALSyntax.Copula.is_first_order(term_linked_concept.term.get_copula()): return related_concepts

                    # if it's first-order, that means the original concept is higher-order
                    # so also try for a related higher-order concept below

                # the initially related concept is compound, not atomic, so we can't just peek the term links once
                # we need to search until we find a statement concept
                related_concept = None
                attempts = 0
                while attempts < Config.NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_CONCEPT \
                    and (related_concept is None \
                    or not isinstance(related_concept.term, NALGrammar.Terms.StatementTerm)):
                    related_concept_item = term_linked_concept.term_links.peek()

                    if related_concept_item is not None: related_concept = related_concept_item.object
                    attempts += 1
                if related_concept is not None and isinstance(related_concept.term,
                                                                  NALGrammar.Terms.StatementTerm): related_concepts.append(related_concept)


        return related_concepts

    def get_random_link(self, concept):
        """
            Randomly gets a term link, prediction link, or explanation link to/from this concept.
            :param concept: A concept representing an first-order statement
            :return: An immediately linked concept
        """
        if len(concept.term_links) > 0 \
                and len(concept.prediction_links) > 0\
                and len(concept.explanation_links) > 0:
            # the concept has every type of link
            rand = random.randint(1, 3)
            if rand == 1:  # peek term link
                links_to_peek = concept.term_links
            elif rand == 2:  # peek prediction links
                links_to_peek = concept.prediction_links
            else:  # peek explanation links
                links_to_peek = concept.explanation_links
        elif len(concept.term_links) == 0 \
                and len(concept.prediction_links) > 0\
                and len(concept.explanation_links) > 0:
                # the concept has no term links
                # there are both predictions and explanations
                rand = random.randint(0,1)
                if rand == 0:
                    links_to_peek = concept.explanation_links
                else:
                    links_to_peek = concept.prediction_links
        elif len(concept.term_links) > 0 \
             and len(concept.prediction_links) == 0 \
             and len(concept.explanation_links) > 0:
            # the concept has no prediction links
            # there are both term links and explanations
            rand = random.randint(0,1)
            if rand == 0:
                links_to_peek = concept.explanation_links
            else:
                links_to_peek = concept.term_links
        elif len(concept.term_links) > 0 \
             and len(concept.prediction_links) > 0 \
             and len(concept.explanation_links) == 0:
            # the concept has no explanation links
            # there are both term links and predictions
            rand = random.randint(0,1)
            if rand == 0:
                links_to_peek = concept.prediction_links
            else:
                links_to_peek = concept.term_links
        elif len(concept.term_links) > 0 \
             and len(concept.prediction_links) == 0 \
             and len(concept.explanation_links) == 0:
            # only term links
            links_to_peek = concept.term_links
        elif len(concept.term_links) == 0 \
             and len(concept.prediction_links) > 0 \
             and len(concept.explanation_links) == 0:
            # only prediction links
            links_to_peek = concept.prediction_links
        elif len(concept.term_links) > 0 \
             and len(concept.prediction_links) > 0 \
             and len(concept.explanation_links) == 0:
            # only explanation links
            links_to_peek = concept.explanation_links
        else:
            return None

        return links_to_peek.peek()

    def get_next_stamp_id(self) -> int:
        """
            :return: next available Stamp ID
        """
        self.next_stamp_id += 1
        return self.next_stamp_id - 1

    def get_next_percept_id(self) -> int:
        """
            :return: next available Percept ID
        """
        self.next_percept_id += 1
        return self.next_percept_id - 1


class Concept:
    """
        NARS Concept
    """
    def __init__(self, term):
        Asserts.assert_term(term)
        self.term = term  # concept's unique term
        self.term_links = NARSDataStructures.Bag.Bag(item_type=Concept)  # Bag of related concepts (related by term)
        self.belief_table = NARSDataStructures.Other.Table(NALGrammar.Sentences.Judgment)
        self.desire_table = NARSDataStructures.Other.Table(NALGrammar.Sentences.Goal)
        self.prediction_links = NARSDataStructures.Bag.Bag(item_type=Concept)
        self.explanation_links = NARSDataStructures.Bag.Bag(item_type=Concept)

    def __str__(self):
        return self.get_formatted_string()

    def __eq__(self, other):
        return self.get_formatted_string() == other.get_formatted_string()

    def get_term(self):
        return self.term

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
        self.term_links.take_using_key(key=NARSDataStructures.ItemContainers.Item.get_key_from_object(concept))
        concept.term_links.take_using_key(key=NARSDataStructures.ItemContainers.Item.get_key_from_object(self))

    def set_prediction_link(self, concept):
        """
            Set a bidirectional term link between 2 concepts, by placing the concept into
            the term links bag.
            Does nothing if the link already exists
        """
        assert_concept(concept)
        if concept in self.prediction_links: return  # already linked
        self.prediction_links.put_new(concept)
        concept.prediction_links.put_new(self)

    def remove_prediction_link(self, concept):
        """
            Remove a bidirectional term link between this concept and another concept
            todo: use this somewhere
        """
        assert_concept(concept)
        assert (concept in self.prediction_links), concept + "must be in prediction links."
        self.prediction_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(concept))
        concept.prediction_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(self))

    def set_explanation_link(self, concept):
        """
            Set a bidirectional term link between 2 concepts, by placing the concept into
            the term links bag.
            Does nothing if the link already exists
        """
        assert_concept(concept)
        if concept in self.explanation_links: return  # already linked
        self.explanation_links.put_new(concept)
        concept.explanation_links.put_new(self)

    def remove_explanation_link(self, concept):
        """
            Remove a bidirectional term link between this concept and another concept
            todo: use this somewhere
        """
        assert_concept(concept)
        assert (concept in self.explanation_links), concept + "must be in prediction links."
        self.explanation_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(concept))
        concept.explanation_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(self))

    def get_formatted_string(self):
        """
            A concept is named by its term
        """
        return self.term.get_formatted_string()


# Asserts
def assert_concept(c):
    assert (isinstance(c, Concept)), str(c) + " must be a Concept"
