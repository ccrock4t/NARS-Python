"""
    Author: Christian Hahm
    Created: March 8, 2021
    Purpose: Given premises, performs proper inference and returns the resultant sentences as Tasks.
"""
import Asserts
import Config
import NALGrammar
import NALInferenceRules.Immediate
import NALInferenceRules.Syllogistic
import NALInferenceRules.Composition
import NALInferenceRules.Local
import NALInferenceRules.Conditional
import NARSDataStructures.Other
import NALSyntax

def do_semantic_inference_two_premise(j1: NALGrammar.Sentences, j2: NALGrammar.Sentences) -> [NARSDataStructures.Other.Task]:
    """
        Derives a new task by performing the appropriate inference rules on the given semantically related sentences.
        The resultant sentence's evidential base is merged from its parents.

        :param j1: Sentence (Goal, Question, or Judgment)
        :param j2: Semantically related belief (Judgment)

        :assume j1 and j2 have distinct evidential bases B1 and B2: B1 ⋂ B2 = Ø
                (no evidential overlap)

        :returns An array of the derived Tasks, or an empty array if the inputs have evidential overlap
    """
    Asserts.assert_sentence(j1)
    Asserts.assert_sentence(j2)

    if j1.statement.connector is not None or j2.statement.connector is not None:
        return []

    """
    ===============================================
    ===============================================
        Pre-Processing
    ===============================================
    ===============================================
    """
    all_derived_sentences = []

    j1_statement = j1.statement
    j2_statement = j2.statement
    j1_subject_term = j1.statement.get_subject_term()
    j2_subject_term = j2.statement.get_subject_term()
    j1_predicate_term = j1.statement.get_predicate_term()
    j2_predicate_term = j2.statement.get_predicate_term()
    j1_copula = j1.statement.get_copula()
    j2_copula = j2.statement.get_copula()
    j1_is_array = j1.is_array
    j2_is_array = j2.is_array

    # check if the result will lead to tautology
    tautology = (j1_subject_term == j2_predicate_term and j1_predicate_term == j2_subject_term) or\
                (j1_subject_term == j2_subject_term and j1_predicate_term == j2_predicate_term
                 and
                 ((not NALSyntax.Copula.is_symmetric(j1_copula) and NALSyntax.Copula.is_symmetric(j2_copula)) # S-->P and P<->S
                 or
                 (NALSyntax.Copula.is_symmetric(j1_copula) and not NALSyntax.Copula.is_symmetric(j2_copula)))) # S<->P and S-->P

    if tautology:
        if Config.DEBUG: print("tautology")
        return [] # can't do inference, it will result in tautology


    # Time Projection between j1 and j2
    # j2 is projected to be used with j1
    if isinstance(j1, NALGrammar.Sentences.Judgment):
        if j1.value.frequency == 0 and j2.value.frequency == 0: return [] # can't do inference with 2 entirely negative premises
        if j2.is_event():
            eternalized_j2 = NALInferenceRules.Local.Eternalization(j2)
            if j1.is_event():
                projected_j2 = NALInferenceRules.Local.Projection(j2, j1.stamp.occurrence_time)
                if projected_j2.value.confidence > eternalized_j2.value.confidence:
                    j2 = projected_j2
                else:
                    j2 = eternalized_j2
            else:
                j2 = eternalized_j2

    """
    ===============================================
    ===============================================
        First-order and Higher-Order Syllogistic Rules
    ===============================================
    ===============================================
    """
    swapped = False

    if NALSyntax.Copula.is_first_order(j1_copula) == NALSyntax.Copula.is_first_order(j2_copula):
        if j1_statement == j2_statement:
            """
            # Revision
            # j1 = j2
            """
            if isinstance(j1, NALGrammar.Sentences.Question): return all_derived_sentences # can't do revision with questions

            derived_sentence = NALInferenceRules.Local.Revision(j1, j2)  # S-->P
            add_to_derived_sentences(derived_sentence,all_derived_sentences)
        elif not NALSyntax.Copula.is_symmetric(j1_copula) and not NALSyntax.Copula.is_symmetric(j2_copula):
            if j1_subject_term == j2_predicate_term or j1_predicate_term == j2_subject_term:
                """
                # j1 = M-->P, j2 = S-->M
                # or j1 = M-->S, j2 = P-->M
                # OR swapped premises
                # j1 = S-->M, j2 = M-->P
                # or j1 = P-->M, j2 = M-->S
                """
                if j1_subject_term != j2_predicate_term:
                    """
                        j1=S-->M, j2=M-->P
                        or j1=P-->M, j2=M-->S
                    """
                    # swap sentences
                    j1, j2 = j2, j1
                    j1_is_array, j2_is_array = j2_is_array, j1_is_array
                    j1_statement, j2_statement, j1_subject_term, j2_subject_term = j2_statement, j1_statement, j2_subject_term, j1_subject_term
                    j1_predicate_term, j2_predicate_term, j1_copula, j2_copula = j2_predicate_term, j1_predicate_term, j2_copula, j1_copula
                    swapped = True

                if not j1_is_array and not j2_is_array:
                    """
                    # Deduction
                    """

                    derived_sentence = NALInferenceRules.Syllogistic.Deduction(j1, j2)  # S-->P or P-->S
                    add_to_derived_sentences(derived_sentence,all_derived_sentences)

                    """
                    # Swapped Exemplification
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Exemplification(j2, j1)  # P-->S or S-->P
                    add_to_derived_sentences(derived_sentence,all_derived_sentences)

            elif j1_subject_term == j2_subject_term:
                """
                    j1=M-->P
                    j2=M-->S
                """
                if not j1_is_array and not j2_is_array:
                    """
                    # Induction
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Induction(j1, j2)  # S-->P
                    add_to_derived_sentences(derived_sentence, all_derived_sentences)

                    """
                    # Swapped Induction
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Induction(j2, j1)  # P-->S
                    add_to_derived_sentences(derived_sentence,all_derived_sentences)

                    """
                    # Comparison
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Comparison(j1, j2)  # S<->P
                    add_to_derived_sentences(derived_sentence,all_derived_sentences)

                    """
                    # Intensional Intersection or Disjunction
                    """
                    derived_sentence = NALInferenceRules.Composition.DisjunctionOrIntensionalIntersection(j1, j2)  # M --> (S | P)
                    add_to_derived_sentences(derived_sentence,all_derived_sentences)

                    """
                    # Extensional Intersection or Conjunction
                    """
                    derived_sentence = NALInferenceRules.Composition.ConjunctionOrExtensionalIntersection(j1, j2)  # M --> (S & P)
                    add_to_derived_sentences(derived_sentence,all_derived_sentences)

                    """
                    # Extensional Difference
                    """
                    derived_sentence = NALInferenceRules.Composition.ExtensionalDifference(j1, j2)  # M --> (S - P)
                    add_to_derived_sentences(derived_sentence,all_derived_sentences)

                    """
                    # Swapped Extensional Difference
                    """
                    derived_sentence = NALInferenceRules.Composition.ExtensionalDifference(j2, j1)  # M --> (P - S)
                    add_to_derived_sentences(derived_sentence,all_derived_sentences)
            elif j1_predicate_term == j2_predicate_term:
                """
                    j1 = P-->M
                    j2 = S-->M
                """

                """
                # Abduction
                """
                derived_sentence = NALInferenceRules.Syllogistic.Abduction(j1, j2)  # S-->P or S==>P
                add_to_derived_sentences(derived_sentence,all_derived_sentences)

                """
                # Swapped Abduction
                """
                derived_sentence = NALInferenceRules.Syllogistic.Abduction(j2, j1)  # P-->S or P==>S
                add_to_derived_sentences(derived_sentence,all_derived_sentences)

                if not NALSyntax.Copula.is_first_order(j1_copula):
                    # two implication statements
                    if NALSyntax.TermConnector.is_conjunction(j1_subject_term.connector) or \
                            NALSyntax.TermConnector.is_conjunction(j2_subject_term.connector):
                        j1_subject_statement_terms = j1_subject_term.subterms if NALSyntax.TermConnector.is_conjunction(
                            j1_subject_term.connector) else [j1_subject_term]

                        j2_subject_statement_terms = j2_subject_term.subterms if NALSyntax.TermConnector.is_conjunction(
                            j2_subject_term.connector) else [j2_subject_term]

                        if len(j1_subject_statement_terms) > len(j2_subject_statement_terms):
                            difference_of_subterms = list(set(j1_subject_statement_terms) - set(j2_subject_statement_terms))
                        else:
                            difference_of_subterms = list(set(j2_subject_statement_terms) - set(j1_subject_statement_terms))

                        if len(difference_of_subterms) == 1:
                            """
                               At least one of the statement's subjects is conjunctive and differs from the
                               other statement's subject by 1 term
                            """
                            if len(j1_subject_statement_terms) > len(j2_subject_statement_terms):
                                derived_sentence = NALInferenceRules.Conditional.ConditionalConjunctionalAbduction(j1,j2)  # S
                            else:
                                derived_sentence = NALInferenceRules.Conditional.ConditionalConjunctionalAbduction(j2,j1)  # S
                            add_to_derived_sentences(derived_sentence,all_derived_sentences)

                """
                # Intensional Intersection Disjunction
                """
                derived_sentence = NALInferenceRules.Composition.DisjunctionOrIntensionalIntersection(j1, j2)  # (P | S) --> M
                add_to_derived_sentences(derived_sentence,all_derived_sentences)

                """
                # Extensional Intersection Conjunction
                """
                derived_sentence = NALInferenceRules.Composition.ConjunctionOrExtensionalIntersection(j1, j2)  # (P & S) --> M
                add_to_derived_sentences(derived_sentence,all_derived_sentences)

                """
                # Intensional Difference
                """
                derived_sentence = NALInferenceRules.Composition.IntensionalDifference(j1, j2)  # (P ~ S) --> M
                add_to_derived_sentences(derived_sentence,all_derived_sentences)

                """
                # Swapped Intensional Difference
                """
                derived_sentence = NALInferenceRules.Composition.IntensionalDifference(j2, j1)  # (S ~ P) --> M
                add_to_derived_sentences(derived_sentence,all_derived_sentences)
                """
                # Comparison
                """
                derived_sentence = NALInferenceRules.Syllogistic.Comparison(j1, j2)  # S<->P or S<=>P
                add_to_derived_sentences(derived_sentence,all_derived_sentences)
        elif not NALSyntax.Copula.is_symmetric(j1_copula) and NALSyntax.Copula.is_symmetric(j2_copula):
            """
            # j1 = M-->P or P-->M
            # j2 = S<->M or M<->S
            # Analogy
            """
            derived_sentence = NALInferenceRules.Syllogistic.Analogy(j1, j2)  # S-->P or P-->S
            add_to_derived_sentences(derived_sentence,all_derived_sentences)
        elif NALSyntax.Copula.is_symmetric(j1_copula) and not NALSyntax.Copula.is_symmetric(j2_copula):
            """
            # j1 = M<->S or S<->M
            # j2 = P-->M or M-->P
            # Swapped Analogy
            """
            derived_sentence = NALInferenceRules.Syllogistic.Analogy(j2, j1)  # S-->P or P-->S
            add_to_derived_sentences(derived_sentence,all_derived_sentences)
        elif NALSyntax.Copula.is_symmetric(j1_copula) and NALSyntax.Copula.is_symmetric(j2_copula):
            """
            # j1 = M<->P or P<->M
            # j2 = S<->M or M<->S
            # Resemblance
            """
            derived_sentence = NALInferenceRules.Syllogistic.Resemblance(j1, j2)  # S<->P
            add_to_derived_sentences(derived_sentence,all_derived_sentences)
    else:
        # They do not have the same-order copula
        """
            j1 = S==>P or S<=>P
            j2 = A-->B or A<->B
            OR
            j1 = A-->B or A<->B
            j2 = S==>P or S<=>P
        """
        if NALSyntax.Copula.is_first_order(j1_copula):
            """
                j1 = A-->B or A<->B 
                j2 = S==>P or S<=>P
            """
            # swap sentences
            j1, j2 = j2, j1
            j1_is_array, j2_is_array = j2_is_array, j1_is_array
            j1_statement, j2_statement,j1_subject_term, j2_subject_term  = j2_statement, j1_statement,j2_subject_term, j1_subject_term
            j1_predicate_term, j2_predicate_term,j1_copula, j2_copula = j2_predicate_term, j1_predicate_term,j2_copula, j1_copula
            swapped = True

        """
            j1 = S==>P or S<=>P
        """
        if NALSyntax.Copula.is_symmetric(j1_copula) and (j2_statement == j1_subject_term or j2_statement == j1_predicate_term) :
            """
                j1 = S<=>P
                j2 = S (e.g A-->B)
            """
            derived_sentence = NALInferenceRules.Conditional.ConditionalAnalogy(j2, j1)  # P
            add_to_derived_sentences(derived_sentence,all_derived_sentences)
        else:
            """
                j1 = S==>P
                j2 = S or P (e.g A-->B)
            """
            if j2_statement == j1_subject_term:
                """
                    j2 = S
                """
                derived_sentence = NALInferenceRules.Conditional.ConditionalDeduction(j1, j2)  # P
                add_to_derived_sentences(derived_sentence,all_derived_sentences)
            elif j2_statement == j1_predicate_term:
                """
                    j2 = P
                """
                derived_sentence = NALInferenceRules.Conditional.ConditionalAbduction(j1, j2)  # S
                add_to_derived_sentences(derived_sentence,all_derived_sentences)
            elif NALSyntax.TermConnector.is_conjunction(j1_subject_term.connector) and not NALSyntax.Copula.is_symmetric(j1_copula):
                """
                    j1 = (C1 && C2 && ..CN && S) ==> P
                    j2 = S
                """
                derived_sentence = NALInferenceRules.Conditional.ConditionalConjunctionalDeduction(j1,j2)  # (C1 && C2 && ..CN) ==> P
                add_to_derived_sentences(derived_sentence,all_derived_sentences)

        if swapped:
            # restore sentences
            j1, j2 = j2, j1
            j1_is_array, j2_is_array = j2_is_array, j1_is_array
            j1_statement, j2_statement,j1_subject_term, j2_subject_term = j2_statement, j1_statement,j2_subject_term, j1_subject_term
            j1_predicate_term, j2_predicate_term,j1_copula, j2_copula = j2_predicate_term, j1_predicate_term,j2_copula, j1_copula
            swapped = False

    """
    ===============================================
    ===============================================
        Post-Processing
    ===============================================
    ===============================================
    """
    # mark sentences as interacted with each other
    j1.stamp.mutually_add_to_interacted_sentences(j2)

    return all_derived_sentences

def add_to_derived_sentences(derived_sentence,derived_sentence_array):
    """
        Add derived sentence to array if it meets certain conditions
    :param derived_sentence:
    :param derived_sentence_array:
    :return:
    """
    if not isinstance(derived_sentence, NALGrammar.Sentences.Question) and derived_sentence.value.confidence == 0.0: return # zero confidence is useless
    derived_sentence_array.append(derived_sentence)

def do_temporal_inference_two_premise(A: NALGrammar.Sentences, B: NALGrammar.Sentences) -> [NARSDataStructures.Other.Task]:
    derived_sentences = []

    derived_sentence = NALInferenceRules.Conditional.ConditionalInduction(A, B) # A =|> B or A =/> B or B =/> A
    derived_sentences.append(derived_sentence)

    derived_sentence = NALInferenceRules.Conditional.ConditionalComparison(A, B) # A <|> B or  A </> B or B </> A
    derived_sentences.append(derived_sentence)

    """
    ===============================================
    ===============================================
        Post-Processing
    ===============================================
    ===============================================
    """


    return derived_sentences


def do_inference_one_premise(j):
    """
        Immediate Inference Rules
        Generates beliefs that are equivalent to j but in a different form.

        :param j: Sentence

        :returns An array of the derived Tasks
    """
    derived_sentences = []

    if j.statement.get_statement_connector() is not None: return derived_sentences

    if isinstance(j, NALGrammar.Sentences.Judgment):
        # Negation (--,(S-->P))
        derived_sentence = NALInferenceRules.Immediate.Negation(j)
        derived_sentences.append(derived_sentence)

        # Conversion (P --> S) or (P ==> S)
        if not j.stamp.from_one_premise_inference \
                and not NALSyntax.Copula.is_symmetric(j.statement.get_copula()) \
                and j.value.frequency > 0:
            derived_sentence = NALInferenceRules.Immediate.Conversion(j)
            derived_sentences.append(derived_sentence)

        # Contraposition  ((--,P) ==> (--,S))
        if j.statement.get_copula() == NALSyntax.Copula.Implication and j.value.frequency < 1:
            derived_sentence = NALInferenceRules.Immediate.Contraposition(j)
            derived_sentences.append(derived_sentence)

        # Image
        if isinstance(j.statement.get_subject_term(), NALGrammar.Terms.CompoundTerm) \
            and j.statement.get_subject_term().connector == NALSyntax.TermConnector.Product\
                and j.statement.get_copula() == NALSyntax.Copula.Inheritance:
            derived_sentence_list = NALInferenceRules.Immediate.ExtensionalImage(j)
            for derived_sentence in derived_sentence_list:
                derived_sentences.append(derived_sentence)
        elif isinstance(j.statement.get_predicate_term(), NALGrammar.Terms.CompoundTerm) \
            and j.statement.get_predicate_term().connector == NALSyntax.TermConnector.Product:
            derived_sentence_list = NALInferenceRules.Immediate.IntensionalImage(j)
            for derived_sentence in derived_sentence_list:
                derived_sentences.append(derived_sentence)

    return derived_sentences