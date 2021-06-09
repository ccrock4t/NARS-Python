import random

import Config
import Global
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
    next_percept_id = 0

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
        NALGrammar.Asserts.assert_term(term)
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
        if isinstance(term, NALGrammar.Terms.VariableTerm): return None #todo created concepts for closed variable terms
        if isinstance(term,NALGrammar.Terms.ArrayTermElementTerm) \
                or (isinstance(term,NALGrammar.Terms.StatementTerm) \
                and isinstance(term.get_subject_term(),NALGrammar.Terms.CompoundTerm)
                and isinstance(term.get_subject_term().subterms[0], NALGrammar.Terms.ArrayTermElementTerm)): return None  # todo created concepts for closed variable terms
        concept_key = NARSDataStructures.ItemContainer.Item.get_key_from_object(term)
        concept_item: NARSDataStructures.ItemContainer.Item = self.concepts_bag.peek(concept_key)
        if concept_item is not None:
            return concept_item.object  # return if it already exists

        # it doesn't exist
        # it must be created along with its sub-concepts if necessary
        if not isinstance(term, NALGrammar.Terms.VariableTerm):
            concept = self.conceptualize_term(term)

        if isinstance(term, NALGrammar.Terms.CompoundTerm):
            for subterm in term.subterms:
                # get/create subterm concepts
                if not isinstance(subterm, NALGrammar.Terms.VariableTerm) \
                    and not isinstance(subterm, NALGrammar.Terms.ArrayTermElementTerm) \
                    and (not isinstance(subterm, NALGrammar.Terms.Array) or isinstance(subterm, NALGrammar.Terms.ArrayTerm)): # don't create concepts for variables or array elements
                    subconcept = self.peek_concept(subterm)
                    # do term linking with subterms
                    concept.set_term_link(subconcept)

        if isinstance(term, NALGrammar.Terms.StatementTerm) and \
                term.copula is not None and\
                not NALSyntax.Copula.is_first_order(term.get_copula()):
            # implication statement
            subject_concept = self.peek_concept(term.get_subject_term())
            predicate_concept = self.peek_concept(term.get_predicate_term())

            # do prediction/explanation linking with subterms
            subject_concept.set_prediction_link(predicate_concept)
            predicate_concept.set_explanation_link(subject_concept)

        return concept

    def get_semantically_related_concept(self, statement_concept):
        """
            Get a concept (named by a Statement Term) that is semantically related to the given concept by a term.
            This can return the given concept in rare cases where no other semantically related concept is found

            :param statement_concept - Statement-Term Concept for which to find a semantically related Statement-Term concept

            :return Statement-Term Concept semantically related to param: `concept`; None if couldn't find any such statement concept
        """
        if len(statement_concept.term_links) == 0: return statement_concept
        related_concept_item = statement_concept.term_links.peek()
        initial_related_concept: Concept = related_concept_item.object
        related_concept = None

        if isinstance(initial_related_concept.term, NALGrammar.Terms.AtomicTerm):
            related_concept_item = initial_related_concept.term_links.peek()
            related_concept = related_concept_item.object
        else:
            # the initially related concept is compound, not atomic
            attempts = 0
            while attempts < Config.NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_CONCEPT \
                and (related_concept is None \
                or not isinstance(related_concept.term, NALGrammar.Terms.StatementTerm)):
                related_concept_item = self.get_random_link(initial_related_concept)

                if related_concept_item is not None: related_concept = related_concept_item.object
                attempts += 1

        if related_concept is not None and not isinstance(related_concept.term, NALGrammar.Terms.StatementTerm): related_concept = None # only return statement concepts

        return related_concept

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
        NALGrammar.Asserts.assert_term(term)
        self.term = term  # concept's unique term
        self.term_links = NARSDataStructures.Bag(item_type=Concept)  # Bag of related concepts (related by term)
        self.belief_table = NARSDataStructures.Table(NALGrammar.Sentences.Judgment)
        self.desire_table = NARSDataStructures.Table(NALGrammar.Sentences.Goal)
        self.prediction_links = NARSDataStructures.Bag(item_type=Concept)
        self.explanation_links = NARSDataStructures.Bag(item_type=Concept)

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
        self.term_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(concept))
        concept.term_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(self))

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
