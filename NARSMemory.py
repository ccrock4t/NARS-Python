import random
import time

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
        self.concepts_bag = NARSDataStructures.Bag.Bag(item_type=Concept,capacity=Config.MEMORY_CONCEPT_CAPACITY)
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
        if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
        self.concepts_bag.put_new(new_concept)
        if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
            "Put new concept item took " + str((time.time() - before) * 1000) + "ms")

        if isinstance(term, NALGrammar.Terms.CompoundTerm):
            for subterm in term.subterms:
                # get/create subterm concepts
                if not isinstance(subterm, NALGrammar.Terms.VariableTerm) \
                        and not isinstance(subterm,
                                           NALGrammar.Terms.ArrayTermElementTerm):  # don't create concepts for variables or array elements
                    subconcept = self.peek_concept(subterm)
                    # do term linking with subterms
                    new_concept.set_term_link(subconcept)

        elif isinstance(term, NALGrammar.Terms.StatementTerm):
            subject_concept = self.peek_concept(term.get_subject_term())
            predicate_concept = self.peek_concept(term.get_predicate_term())

            if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
            subject_concept.set_term_link(new_concept)
            predicate_concept.set_term_link(new_concept)
            if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
                "Set term links concept item took " + str((time.time() - before) * 1000) + "ms")

            if not term.is_first_order():
                # implication statement
                # do prediction/explanation linking with subterms
                if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
                subject_concept.set_prediction_link(new_concept)
                predicate_concept.set_explanation_link(new_concept)
                if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
                    "Set implication links concept item took " + str((time.time() - before) * 1000) + "ms")

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
              :return Concept named by the term
          """
        if isinstance(term, NALGrammar.Terms.VariableTerm): return None #todo created concepts for closed variable terms
        if isinstance(term,NALGrammar.Terms.ArrayTermElementTerm) \
                or (isinstance(term,NALGrammar.Terms.StatementTerm) \
                and isinstance(term.get_subject_term(),NALGrammar.Terms.CompoundTerm)
                and isinstance(term.get_subject_term().subterms[0], NALGrammar.Terms.ArrayTermElementTerm)): return None  # todo created concepts for closed variable terms

        # try to find the existing concept
        concept_key = NARSDataStructures.ItemContainers.Item.get_key_from_object(term)

        if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
        concept_item: NARSDataStructures.ItemContainers.Item = self.concepts_bag.peek(concept_key)
        if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
            "Peek concept item took " + str((time.time() - before) * 1000) + "ms")

        if concept_item is not None:
            return concept_item  # return if it already exists

        # it doesn't exist
        # it must be created along with its sub-concepts if necessary
        if Config.DEBUG or Config.TIMING_DEBUG: before = time.time()
        concept_item = self.conceptualize_term(term)
        if Config.DEBUG or Config.TIMING_DEBUG: Global.Global.debug_print(
            "Conceptualize concept item took " + str((time.time() - before) * 1000) + "ms")

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
                    # the term-linked sentence is high-order statement concept
                    # return this statement concept
                    related_concepts.append(term_linked_concept)

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
        possible_link_bags = []
        if len(concept.term_links) > 0:
            possible_link_bags.append(concept.term_links)

        if len(concept.prediction_links) > 0:
            possible_link_bags.append(concept.prediction_links)

        if len(concept.explanation_links) > 0:
            possible_link_bags.append(concept.explanation_links)

        # the concept has every type of link
        links_to_peek = random.choice(possible_link_bags)

        return links_to_peek.peek()

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

            belief = explanation_concept.belief_table.peek()

            if NALGrammar.Sentences.may_interact(j,belief):
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
        MAX_ATTEMPTS = 3
        while count < MAX_ATTEMPTS:
            item = statement_concept.explanation_links.peek()
            explanation_concept: Concept = item.object  # A =/> B

            if explanation_concept.term.get_subject_term().contains_positive():
                # (A &/ B) =/> C and A.
                belief = explanation_concept.belief_table.peek_highest_confidence_interactable(j)
                if belief is None:
                    continue
                else:
                    best_explanation_belief = belief
                    break

            count += 1

        if best_explanation_belief is None:
            item = statement_concept.explanation_links.peek()
            best_explanation_belief = item.object.belief_table.peek_highest_confidence_interactable(j)

        return best_explanation_belief


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

        # update explanation link
        statement_concept.prediction_links.change_priority(prediction_concept_item.key,
                                                  prediction_belief.get_expectation())

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
        explanation_belief = explanation_concept.belief_table.peek_highest_confidence_interactable(j)

        # update explanation link
        if explanation_belief is not None:
            concept.explanation_links.change_priority(explanation_concept_item.key,
                                                      explanation_belief.get_expectation())

        return explanation_belief

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

    def get_best_explanation_with_op_precondition(self, j):
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

            if belief is not None and belief.statement.contains_op():
                if best_belief is None:
                    best_belief = belief
                else:
                    best_belief = NALInferenceRules.Local.Choice(best_belief, belief) # new best belief?

        return best_belief


    def get_prediction_with_highest_desired_postcondition(self, j):
        """
            Returns the best prediction belief and and highest desired postcondition for a given belief
        :param j:
        :return:
        """
        concept = self.peek_concept(j.statement)
        best_prediction = None
        most_desired_prediction, most_desired_postcondition = None, None

        for prediction_concept_item in concept.prediction_links:
            prediction_concept = prediction_concept_item.object
            if len(prediction_concept.belief_table ) == 0: continue
            prediction = prediction_concept.belief_table.peek()

            if prediction is not None:
                if best_prediction is None:
                    best_prediction = prediction
                else:
                    best_prediction = NALInferenceRules.Local.Choice(best_prediction, prediction) # new best belief?

                post_condition_concept = self.peek_concept(prediction.statement.get_predicate_term())
                if len(post_condition_concept.desire_table) > 0:
                    if most_desired_prediction is None:
                        most_desired_prediction, most_desired_postcondition = prediction, post_condition_concept.desire_table.peek()
                    else:
                        better_post = NALInferenceRules.Local.Choice(most_desired_postcondition, post_condition_concept.desire_table.peek())  # new best belief?
                        if better_post != most_desired_postcondition:
                            most_desired_prediction, most_desired_postcondition = prediction, better_post


        return [best_prediction,most_desired_prediction]

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
        self.belief_table = NARSDataStructures.Other.Table(NALGrammar.Sentences.Judgment)
        self.desire_table = NARSDataStructures.Other.Table(NALGrammar.Sentences.Goal, capacity=1)
        self.prediction_links = NARSDataStructures.Bag.Bag(item_type=Concept, capacity=Config.CONCEPT_LINK_CAPACITY)
        self.explanation_links = NARSDataStructures.Bag.Bag(item_type=Concept, capacity=Config.CONCEPT_LINK_CAPACITY)

    def __str__(self):
        return self.get_formatted_string()

    def __eq__(self, other):
        return self.get_formatted_string() == other.get_formatted_string()

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

    def get_expectation(self):
        """
            :return: If the highest-confidence belief says this statement is true
        """
        if len(self.belief_table) == 0: return None
        belief = self.belief_table.peek()
        return belief.get_expectation()

    def set_term_link(self, concept):
        """
            Set a bidirectional term link between 2 concepts
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
            Set a prediction link between 2 concepts
            Does nothing if the link already exists
        """
        assert_concept(concept)
        if concept in self.prediction_links: return  # already linked
        self.prediction_links.put_new(concept)

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

    def remove_explanation_link(self, concept):
        """
            Remove a bidirectional term link between this concept and another concept
            todo: use this somewhere
        """
        assert_concept(concept)
        assert (concept in self.explanation_links), concept + "must be in prediction links."
        self.explanation_links.take_using_key(key=NARSDataStructures.ItemContainer.Item.get_key_from_object(concept))

    def get_formatted_string(self):
        """
            A concept is named by its term
        """
        return self.term.get_formatted_string()


# Asserts
def assert_concept(c):
    assert (isinstance(c, Concept)), str(c) + " must be a Concept"

