import random
import timeit as time

import numpy as np

import Asserts
import Config
import Global
import NALGrammar
import NALSyntax
import NARSDataStructures.Bag
import NARSDataStructures.Other
import NARSDataStructures.ItemContainers
import NALInferenceRules
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
        self.concepts_bag = NARSDataStructures.Bag.Bag(item_type=Concept,
                                                       capacity=Config.MEMORY_CONCEPT_CAPACITY,
                                                       granularity=1000)
        self.current_cycle_number = 0

    def __len__(self):
        return self.get_number_of_concepts()

    def get_random_concept(self):
        """
            Probabilistically peek the concepts
        """
        return self.concepts_bag.peek().object

    def get_random_concept_item(self):
        """
            Probabilistically peek the concepts
        """
        return self.concepts_bag.peek()

    def get_number_of_concepts(self):
        """
            Get the number of concepts that exist in memory
        """
        return len(self.concepts_bag)

    def conceptualize_term(self, term):
        """
            Create a new concept from a term and add it to the bag

            :param term: The term naming the concept to create
            :returns New Concept item created from the term
        """
        Asserts.assert_term(term)
        concept_key = NARSDataStructures.ItemContainers.Item.get_key_from_object(term)
        assert not (concept_key in self.concepts_bag.item_lookup_dict), "Cannot create new concept. Concept already exists."
        # create new concept
        new_concept = Concept(term)

        # put into data structure
        self.concepts_bag.put_new(new_concept) # add to bag

        if isinstance(term, NALGrammar.Terms.CompoundTerm) and not isinstance(term, NALGrammar.Terms.SpatialTerm):
            #todo allow array elements
            for i, subterm in np.ndenumerate(term.subterms):
                # get/create subterm concepts
                if not isinstance(subterm, NALGrammar.Terms.VariableTerm):  # don't create concepts for variables or array elements
                    subconcept = self.peek_concept(subterm)
                    # do term linking with subterms
                    new_concept.set_term_links(subconcept)

        elif isinstance(term, NALGrammar.Terms.StatementTerm):
            subject_concept = self.peek_concept(term.get_subject_term())
            predicate_concept = self.peek_concept(term.get_predicate_term())

            new_concept.set_term_links(subject_concept)
            new_concept.set_term_links(predicate_concept)

            if not term.is_first_order():
                # implication statement
                # do prediction/explanation linking with subterms
                subject_concept.set_prediction_link(new_concept)
                predicate_concept.set_explanation_link(new_concept)

        return self.concepts_bag.peek(concept_key)

    def peek_concept(self, term):
        return self.peek_concept_item(term).object

    def peek_concept_item(self, term):
        """
              Peek the concept from memory using its term,
              AND create it if it doesn't exist.
              Also recursively creates all sub-term concepts if they do not exist.

              If it's an `open` variable term, the concept is not created, though if it has sub-terms
               those concepts will be created.

              :param term: The term naming the concept to peek
              :return Concept item named by the term
          """
        if isinstance(term, NALGrammar.Terms.VariableTerm): return None #todo created concepts for closed variable terms

        # try to find the existing concept
        concept_key = NARSDataStructures.ItemContainers.Item.get_key_from_object(term)

        concept_item: NARSDataStructures.ItemContainers.Item = self.concepts_bag.peek(concept_key)

        if concept_item is not None:
            return concept_item  # return if it already exists

        # if it doesn't exist
        # it must be created along with its sub-concepts if necessary
        concept_item = self.conceptualize_term(term)

        return concept_item


    def get_semantically_related_concept(self, statement_concept):
        """
            Get concepts (named by a Statement Term) that are semantically related to the given concept.

            Using term-links, returns a concept with the same copula order; one for the subject and one for the predicate.

            For a first-order statement, may try to instead return higher-order concepts based on implication links

            :param statement_concept - Statement-Term Concept for which to find a semantically related Statement-Term concept

            :return Statement-Term Concepts semantically related to param: `statement_concept`
        """

        count = 0
        related_concept = None
        if len(statement_concept.term_links) == 0: return None
        while count < Config.NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_CONCEPT \
                and (related_concept is None):
            count += 1
            shared_term_concept = statement_concept.term_links.peek().object
            if statement_concept.term.is_first_order():
                # S --> P
                if len(statement_concept.term_links) != 0:
                    shared_term_concept = statement_concept.term_links.peek().object
                    if isinstance(shared_term_concept.term, NALGrammar.Terms.AtomicTerm):
                        # atomic term concept (S)
                        related_concept = shared_term_concept.term_links.peek().object # peek additional term links to get another statement term
                    elif isinstance(shared_term_concept.term, NALGrammar.Terms.CompoundTerm):
                        if shared_term_concept.term.is_first_order():
                            # the subject or predicate is a first-order compound
                            related_concept = shared_term_concept.term_links.peek().object # peek additional term links to get a statement term
                            if not isinstance(related_concept.term, NALGrammar.Terms.StatementTerm): related_concept = None
                        else:
                            # this statement is in a higher-order compound, we can use it in inference
                            related_concept = shared_term_concept
                    elif isinstance(shared_term_concept.term, NALGrammar.Terms.StatementTerm):
                        # implication statement (S-->P) ==> B
                        related_concept = shared_term_concept
            else:
                # S ==> P
                # term linked concept is A-->B
                if len(shared_term_concept.prediction_links) == 0 and len(shared_term_concept.explanation_links) == 0:
                    continue
                elif len(shared_term_concept.prediction_links) != 0 and len(shared_term_concept.explanation_links) == 0:
                    bag = shared_term_concept.prediction_links
                elif len(shared_term_concept.explanation_links) != 0 and len(shared_term_concept.prediction_links) == 0:
                    bag = shared_term_concept.explanation_links
                else:
                    bag = random.choice([shared_term_concept.prediction_links,shared_term_concept.explanation_links])

                related_concept = bag.peek().object

        return related_concept

    def get_best_explanation(self, j):
        """
            Gets the best explanation belief for the given sentence's statement
            that the sentence is able to interact with
        :param statement_concept:
        :return:
        """
        statement_concept: Concept = self.peek_concept(j.statement) # B
        best_explanation_belief = None
        for explanation_concept_item in statement_concept.explanation_links:
            explanation_concept: Concept = explanation_concept_item.object  # A =/> B
            if len(explanation_concept.belief_table) == 0: continue

            belief = explanation_concept.belief_table.peek_highest_confidence_interactable(j)

            if belief is not None:
                if best_explanation_belief is None:
                    best_explanation_belief = belief
                else:
                    best_explanation_belief = NALInferenceRules.Local.Choice(belief, best_explanation_belief)

        return best_explanation_belief

    def get_explanation_preferred_with_true_precondition(self, j):
        """
            Gets the best explanation belief for the given sentence's statement
            that the sentence is able to interact with
        :param statement_concept:
        :return:
        """
        statement_concept: Concept = self.peek_concept(j.statement) # B
        if len(statement_concept.explanation_links) == 0: return
        best_explanation_belief = None
        count = 0
        MAX_ATTEMPTS = Config.NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_BELIEF

        while count < MAX_ATTEMPTS:
            item = statement_concept.explanation_links.peek()
            explanation_concept: Concept = item.object  # A =/> B

            if explanation_concept.term.get_subject_term().contains_positive():
                # (A &/ B) =/> C and A.
                belief = explanation_concept.belief_table.peek()
                if belief is not None:
                    if best_explanation_belief is None:
                        best_explanation_belief = belief
                    else:
                        best_explanation_belief = NALInferenceRules.Local.Choice(belief,best_explanation_belief)

            count += 1

        if best_explanation_belief is None:
            item = statement_concept.explanation_links.peek()
            best_explanation_belief = item.object.belief_table.peek_random()

        return best_explanation_belief

    def get_prediction_preferred_with_true_postcondition(self, j):
        """
            Gets the best explanation belief for the given sentence's statement
            that the sentence is able to interact with
        :param statement_concept:
        :return:
        """
        statement_concept: Concept = self.peek_concept(j.statement) # B
        if len(statement_concept.prediction_links) == 0: return
        best_prediction_belief = None
        count = 0
        MAX_ATTEMPTS = Config.NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_BELIEF
        while count < MAX_ATTEMPTS:
            item = statement_concept.prediction_links.peek()
            prediction_concept: Concept = item.object  # A =/> B

            if prediction_concept.term.get_predicate_term().contains_positive():
                # (A &/ B) =/> C and A.
                belief = prediction_concept.belief_table.peek_highest_confidence_interactable(j)
                if belief is None:
                    continue
                elif best_prediction_belief is None:
                    best_prediction_belief = belief
                    break
            count += 1

        if best_prediction_belief is None:
            item = statement_concept.prediction_links.peek()
            best_prediction_belief = item.object.belief_table.peek_random()

        return best_prediction_belief

    def get_random_bag_prediction(self, j):
        """
            Gets the best explanation belief for the given sentence's statement
            that the sentence is able to interact with
        :param statement_concept:
        :return:
        """
        statement_concept: Concept = self.peek_concept(j.statement) # B
        if len(statement_concept.prediction_links) == 0: return None

        prediction_concept_item = statement_concept.prediction_links.peek()
        prediction_concept = prediction_concept_item.object
        prediction_belief = prediction_concept.belief_table.peek()

        return prediction_belief

    def get_random_bag_explanation(self, j):
        """
            Gets the best explanation belief for the given sentence's statement
            that the sentence is able to interact with
        :param statement_concept:
        :return:
        """
        concept: Concept = self.peek_concept(j.statement) # B
        if len(concept.explanation_links) == 0: return None

        explanation_concept_item = concept.explanation_links.peek()
        explanation_concept = explanation_concept_item.object
        explanation_belief = explanation_concept.belief_table.peek_random()

        return explanation_belief

    def get_random_explanation_preferred_with_true_precondition(self, j):
        """
            Returns random explanation belief
        :param j:
        :return:
        """
        concept = self.peek_concept(j.statement)
        best_belief = None
        count = 0
        MAX_ATTEMPTS = Config.NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_BELIEF
        while count < MAX_ATTEMPTS:
            explanation_concept_item = concept.explanation_links.peek()
            explanation_concept = explanation_concept_item.object
            if len(explanation_concept.belief_table ) == 0: continue
            belief = explanation_concept.belief_table.peek()

            if belief is not None:
                if best_belief is None:
                    best_belief = belief
                else:
                    belief_is_pos_conj = NALSyntax.TermConnector.is_conjunction(
                        belief.statement.get_subject_term().connector) and belief.statement.get_subject_term().contains_positive()

                    best_belief_is_pos_conj = NALSyntax.TermConnector.is_conjunction(
                        best_belief.statement.get_subject_term().connector) and best_belief.statement.get_subject_term().contains_positive()

                    if belief_is_pos_conj and not best_belief_is_pos_conj:
                        best_belief = belief
                    elif best_belief_is_pos_conj and not belief_is_pos_conj:
                        pass
                    else:
                        best_belief = NALInferenceRules.Local.Choice(best_belief, belief) # new best belief?

            count += 1

        return best_belief


    def get_best_prediction(self, j):
        """
            Returns the best prediction belief for a given belief
        :param j:
        :return:
        """
        concept = self.peek_concept(j.statement)
        best_belief = None
        for prediction_concept_item in concept.prediction_links:
            prediction_concept = prediction_concept_item.object
            if len(prediction_concept.belief_table ) == 0: continue
            prediction_belief = prediction_concept.belief_table.peek()

            if prediction_belief is not None:
                if best_belief is None:
                    best_belief = prediction_belief
                else:
                    best_belief = NALInferenceRules.Local.Choice(best_belief, prediction_belief) # new best belief?

        return best_belief

    def get_best_explanation_with_true_precondition(self, j):
        """
            Returns the best prediction belief for a given belief
        :param j:
        :return:
        """
        concept = self.peek_concept(j.statement)
        best_belief = None
        for concept_item in concept.explanation_links:
            concept = concept_item.object
            if len(concept.belief_table ) == 0: continue
            belief = concept.belief_table.peek()

            if belief is not None and\
                NALSyntax.TermConnector.is_conjunction(belief.statement.get_subject_term().connector) and\
                belief.statement.get_subject_term().contains_positive():
                if best_belief is None:
                    best_belief = belief
                else:
                    best_belief = NALInferenceRules.Local.Choice(best_belief, belief) # new best belief?

        return best_belief


    def get_prediction_with_desired_postcondition(self, statement_concept):
        """
            Returns the best prediction belief and and highest desired postcondition for a given belief
        :param j:
        :return:
        """
        prediction_links = statement_concept.prediction_links
        if len(prediction_links) == 0: return None
        best_prediction_belief = None
        count = 0
        MAX_ATTEMPTS = Config.NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_BELIEF
        while count < MAX_ATTEMPTS:
            item = prediction_links.peek()
            prediction_concept: Concept = item.object  # A =/> B

            if self.peek_concept(prediction_concept.term.get_predicate_term()).is_desired():
                # (A &/ B) =/> C and A.
                belief = prediction_concept.belief_table.peek()
                if belief is not None:
                    if best_prediction_belief is None:
                        best_prediction_belief = belief
                    else:
                        best_prediction_belief = NALInferenceRules.Local.Choice(best_prediction_belief, belief)  # new best belief?

            count += 1

        return best_prediction_belief

    def get_random_positive_prediction(self, j):
        """
            Returns a random positive prediction belief for a given belief
        :param j:
        :return:
        """
        concept = self.peek_concept(j.statement)
        positive_beliefs = []
        for prediction_concept_item in concept.prediction_links:
            prediction_concept = prediction_concept_item.object
            if len(prediction_concept.belief_table) == 0: continue
            prediction_belief = prediction_concept.belief_table.peek()

            if prediction_belief is not None:
                if prediction_belief.is_positive():
                    positive_beliefs.append(prediction_belief)

        if len(positive_beliefs) == 0:
            return None
        return positive_beliefs[round(random.random() * (len(positive_beliefs)-1))]

    def get_random_prediction(self, j):
        """
            Returns a random positive prediction belief for a given belief
        :param j:
        :return:
        """
        concept = self.peek_concept(j.statement)
        if len(concept.prediction_links) == 0:
            return None
        prediction_concept = concept.prediction_links.peek().object
        if len(prediction_concept.belief_table) == 0:
            return None
        return prediction_concept.belief_table.peek()

    def get_all_positive_predictions(self, j):
        predictions = []
        concept = self.peek_concept(j.statement)
        for prediction_concept_item in concept.prediction_links:
            prediction_concept = prediction_concept_item.object
            if len(prediction_concept.belief_table ) == 0: continue
            prediction_belief = prediction_concept.belief_table.peek()

            if prediction_belief is not None:
                if isinstance(prediction_belief.statement.get_predicate_term(),NALGrammar.Terms.StatementTerm) and prediction_belief.is_positive():
                    predictions.append(prediction_belief)

        return predictions

    def get_best_positive_desired_prediction(self, concept):
        """
            Returns the best predictive implication from a given concept's prediction links,
            but only accounts those predictions whose postconditions are desired
        :param j:
        :return:
        """
        best_belief = None
        for prediction_concept_item in concept.prediction_links:
            prediction_concept = prediction_concept_item.object
            if len(prediction_concept.belief_table ) == 0: continue
            prediction_belief = prediction_concept.belief_table.peek()

            if prediction_belief is not None and prediction_concept.is_positive():
                postcondition_term = prediction_concept.term.get_predicate_term()
                if isinstance(postcondition_term,NALGrammar.Terms.StatementTerm):
                    if self.peek_concept(postcondition_term).is_desired():
                        if best_belief is None:
                            best_belief = prediction_belief
                        else:
                            best_belief = NALInferenceRules.Local.Choice(best_belief, prediction_belief) # new best belief?

        return best_belief

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
        self.term_links = NARSDataStructures.Bag.Bag(item_type=Concept, capacity=Config.CONCEPT_LINK_CAPACITY)  # Bag of related concepts (related by term)
        self.subterm_links = NARSDataStructures.Bag.Bag(item_type=Concept,
                                                     capacity=Config.CONCEPT_LINK_CAPACITY)  # Bag of related concepts (related by term)
        self.superterm_links = NARSDataStructures.Bag.Bag(item_type=Concept,
                                                     capacity=Config.CONCEPT_LINK_CAPACITY)  # Bag of related concepts (related by term)
        self.belief_table = NARSDataStructures.Other.Table(NALGrammar.Sentences.Judgment)
        self.desire_table = NARSDataStructures.Other.Table(NALGrammar.Sentences.Goal)
        self.prediction_links = NARSDataStructures.Bag.Bag(item_type=Concept, capacity=Config.CONCEPT_LINK_CAPACITY)
        self.explanation_links = NARSDataStructures.Bag.Bag(item_type=Concept, capacity=Config.CONCEPT_LINK_CAPACITY)

    def __str__(self):
        return self.get_term_string()

    def __eq__(self, other):
        return self.get_term_string() == other.get_formatted_string()

    def get_term(self):
        return self.term

    def is_desired(self):
        """
            :return: If the highest-confidence belief says this statement is true
        """
        if len(self.desire_table) == 0: return False
        return NALInferenceRules.Local.Decision(self.desire_table.peek())

    def is_positive(self):
        """
            :return: If the highest-confidence belief says this statement is true
        """
        if len(self.belief_table) == 0: return False
        return self.belief_table.peek().is_positive()

    def term_contains_positive(self):
        if len(self.belief_table) == 0: return False
        return self.belief_table.peek().statement.contains_positive()

    def get_expectation(self):
        """
            :return: If the highest-confidence belief says this statement is true
        """
        if len(self.belief_table) == 0: return None
        belief = self.belief_table.peek()
        return belief.get_expectation()

    def set_term_links(self, subterm_concept):
        """
            Set a bidirectional term link between 2 concepts and the subterm/superterm link
            Does nothing if the link already exists

            :param subterm concept to this superterm concept (self)
        """
        assert_concept(subterm_concept)
        if subterm_concept in self.term_links: return  # already linked

        # add to term links
        item = self.term_links.put_new(subterm_concept)
        self.term_links.change_priority(item.key, new_priority=0.5)

        item = subterm_concept.term_links.put_new(self)
        subterm_concept.term_links.change_priority(item.key, new_priority=0.5)

        # add to subterm links
        item = self.subterm_links.put_new(subterm_concept)
        self.subterm_links.change_priority(item.key, new_priority=0.5)

        # add to superterm links
        item = subterm_concept.superterm_links.put_new(self)
        subterm_concept.superterm_links.change_priority(item.key, new_priority=0.5)

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
            Set a prediction link between 2 concepts
            Does nothing if the link already exists
        """
        assert_concept(concept)
        if concept in self.prediction_links: return  # already linked
        concept_item = self.prediction_links.put_new(concept)
        self.prediction_links.change_priority(concept_item.key, new_priority=0.99)

    def remove_prediction_link(self, concept):
        """
            Remove a bidirectional term link between this concept and another concept
            todo: use this somewhere
        """
        assert_concept(concept)
        assert (concept in self.prediction_links), concept + "must be in prediction links."
        self.prediction_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(concept))

    def set_explanation_link(self, concept):
        """
            Set an explanation between 2 concepts
            Does nothing if the link already exists
        """
        assert_concept(concept)
        if concept in self.explanation_links: return  # already linked
        concept_item = self.explanation_links.put_new(concept)
        self.explanation_links.change_priority(concept_item.key,new_priority=0.99)


    def remove_explanation_link(self, concept):
        """
            Remove a bidirectional term link between this concept and another concept
            todo: use this somewhere
        """
        assert_concept(concept)
        assert (concept in self.explanation_links), concept + "must be in prediction links."
        self.explanation_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(concept))

    def get_term_string(self):
        """
            A concept is named by its term
        """
        return self.term.get_term_string()


# Asserts
def assert_concept(c):
    assert (isinstance(c, Concept)), str(c) + " must be a Concept"

