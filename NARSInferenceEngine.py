"""
    Author: Christian Hahm
    Created: March 8, 2021
    Purpose: Given premises, performs proper inference and returns the resultant sentences as Tasks.
"""
import Global
import NALGrammar
import NALInferenceRules.Immediate
import NALInferenceRules.Syllogistic
import NALInferenceRules.Composition
import NALInferenceRules.Local
import NALInferenceRules.Conditional
import NARSDataStructures
import NALSyntax

def do_semantic_inference_two_premise(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence) -> [NARSDataStructures.Task]:
    """
        Derives a new task by performing the appropriate inference rules on the given semantically related sentences.
        The resultant sentence's evidential base is merged from its parents.

        :param j1: Sentence
        :param j2: Sentence

        :assume j1 and j2 have distinct evidential bases B1 and B2: B1 ⋂ B2 = Ø
                (no evidential overlap)

        :returns An array of the derived Tasks, or an empty array if the inputs have evidential overlap
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    if j1.statement.connector is not None or j2.statement.connector is not None:
        return []

    """
    ===============================================
    ===============================================
        Pre-Processing
    ===============================================
    ===============================================
    """
    derived_sentences = []

    j1_statement = j1.statement
    j2_statement = j2.statement
    j1_subject_term = j1.statement.get_subject_term()
    j2_subject_term = j2.statement.get_subject_term()
    j1_predicate_term = j1.statement.get_predicate_term()
    j2_predicate_term = j2.statement.get_predicate_term()
    j1_copula = j1.statement.get_copula()
    j2_copula = j2.statement.get_copula()

    # check if the result will lead to tautology
    tautology = (j1_subject_term == j2_predicate_term and j1_predicate_term == j2_subject_term) or\
                (j1_subject_term == j2_subject_term and j1_predicate_term == j2_predicate_term
                 and
                 ((not NALSyntax.Copula.is_symmetric(j1_copula) and NALSyntax.Copula.is_symmetric(j2_copula)) # S-->P and P<->S
                 or
                 (NALSyntax.Copula.is_symmetric(j1_copula) and not NALSyntax.Copula.is_symmetric(j2_copula)))) # S<->P and S-->P

    if tautology:
        if Global.Global.DEBUG: print("tautology")
        return [] # can't do inference, it will result in tautology


    # Time Projection between j1 and j2
    # j2 is projected to be used with j1
    if isinstance(j1, NALGrammar.Judgment):
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
    if isinstance(j1, NALGrammar.Judgment) or isinstance(j1, NALGrammar.Question):
        if NALSyntax.Copula.is_first_order(j1_copula) == NALSyntax.Copula.is_first_order(j2_copula):
            if j1_statement == j2_statement:
                """
                # Revision
                # j1 = S-->P, j2 = S-->P
                # or j1 = S<->P, j2 = S<->P
                """
                if isinstance(j1, NALGrammar.Question): return derived_sentences # can't do revision with questions

                derived_sentence = NALInferenceRules.Local.Revision(j1, j2)  # S-->P
                print_inference_rule(inference_rule="Revision")
                derived_sentences.append(derived_sentence)
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
                        j1_statement, j2_statement = j2_statement, j1_statement
                        j1_subject_term, j2_subject_term = j2_subject_term, j1_subject_term
                        j1_predicate_term, j2_predicate_term = j2_predicate_term, j1_predicate_term
                        j1_copula, j2_copula = j2_copula, j1_copula
                        swapped = True
                    """
                    # Deduction
                    """

                    derived_sentence = NALInferenceRules.Syllogistic.Deduction(j1, j2)  # S-->P or P-->S
                    print_inference_rule(inference_rule="Deduction")
                    derived_sentences.append(derived_sentence)

                    """
                    # Swapped Exemplification
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Exemplification(j2, j1)  # P-->S or S-->P
                    print_inference_rule(inference_rule="Swapped Exemplification")
                    derived_sentences.append(derived_sentence)

                    if swapped:
                        # restore sentences
                        j1, j2 = j2, j1
                        j1_statement, j2_statement = j2_statement, j1_statement
                        j1_subject_term, j2_subject_term = j2_subject_term, j1_subject_term
                        j1_predicate_term, j2_predicate_term = j2_predicate_term, j1_predicate_term
                        j1_copula, j2_copula = j2_copula, j1_copula
                        swapped = False
                elif j1_subject_term == j2_subject_term:
                    """
                        j1=M-->P
                        j2=M-->S
                    # Induction
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Induction(j1, j2)  # S-->P
                    print_inference_rule(inference_rule="Induction")
                    derived_sentences.append(derived_sentence)

                    """
                    # Swapped Induction
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Induction(j2, j1)  # P-->S
                    print_inference_rule(inference_rule="Swapped Induction")
                    derived_sentences.append(derived_sentence)

                    """
                    # Comparison
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Comparison(j1, j2)  # S<->P
                    print_inference_rule(inference_rule="Comparison")
                    derived_sentences.append(derived_sentence)

                    """
                    # Intensional Intersection or Disjunction
                    """
                    derived_sentence = NALInferenceRules.Composition.IntensionalIntersectionOrDisjunction(j1, j2)  # M --> (S | P)
                    print_inference_rule(inference_rule="Intensional Intersection or Disjunction")
                    derived_sentences.append(derived_sentence)

                    """
                    # Extensional Intersection or Conjunction
                    """
                    derived_sentence = NALInferenceRules.Composition.ExtensionalIntersectionOrConjunction(j1, j2)  # M --> (S & P)
                    print_inference_rule(inference_rule="Extensional Intersection or Conjunction")
                    derived_sentences.append(derived_sentence)

                    """
                    # Extensional Difference
                    """
                    derived_sentence = NALInferenceRules.Composition.ExtensionalDifference(j1, j2)  # M --> (S - P)
                    print_inference_rule(inference_rule="Extensional Difference")
                    derived_sentences.append(derived_sentence)

                    """
                    # Swapped Extensional Difference
                    """
                    derived_sentence = NALInferenceRules.Composition.ExtensionalDifference(j2, j1)  # M --> (P - S)
                    print_inference_rule( inference_rule="Extensional Difference")
                    derived_sentences.append(derived_sentence)
                elif j1_predicate_term == j2_predicate_term:
                    """
                        j1 = P-->M
                        j2 = S-->M
                    # Abduction
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Abduction(j1, j2)  # S-->P or S==>P
                    print_inference_rule(inference_rule="Abduction")
                    derived_sentences.append(derived_sentence)

                    """
                    # Swapped Abduction
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Abduction(j2, j1)  # P-->S or P==>S
                    print_inference_rule(inference_rule="Swapped Abduction")
                    derived_sentences.append(derived_sentence)

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
                                print_inference_rule(inference_rule="Conditional Conjunctional Abduction")
                                derived_sentences.append(derived_sentence)

                    """
                    # Comparison
                    """
                    derived_sentence = NALInferenceRules.Syllogistic.Comparison(j1, j2)  # S<->P or S<=>P
                    print_inference_rule(inference_rule="Comparison")
                    derived_sentences.append(derived_sentence)

                    """
                    # Intensional Intersection Disjunction
                    """
                    derived_sentence = NALInferenceRules.Composition.IntensionalIntersectionOrDisjunction(j1, j2)  # (P | S) --> M
                    print_inference_rule(inference_rule="Intensional Intersection")
                    derived_sentences.append(derived_sentence)

                    """
                    # Extensional Intersection Conjunction
                    """
                    derived_sentence = NALInferenceRules.Composition.ExtensionalIntersectionOrConjunction(j1, j2)  # (P & S) --> M
                    print_inference_rule(inference_rule="Extensional Intersection")
                    derived_sentences.append(derived_sentence)

                    """
                    # Intensional Difference
                    """
                    derived_sentence = NALInferenceRules.Composition.IntensionalDifference(j1, j2)  # (P ~ S) --> M
                    print_inference_rule(inference_rule="Intensional Difference")
                    derived_sentences.append(derived_sentence)

                    """
                    # Swapped Intensional Difference
                    """
                    derived_sentence = NALInferenceRules.Composition.IntensionalDifference(j2, j1)  # (S ~ P) --> M
                    print_inference_rule(inference_rule="Swapped Intensional Difference")
                    derived_sentences.append(derived_sentence)
                else:
                    assert False, "error, concept " + str(j1.statement) + " and " + str(j2.statement) + " not related"
            elif not NALSyntax.Copula.is_symmetric(j1_copula) and NALSyntax.Copula.is_symmetric(j2_copula):
                """
                # j1 = M-->P or P-->M
                # j2 = S<->M or M<->S
                # Analogy
                """
                derived_sentence = NALInferenceRules.Syllogistic.Analogy(j1, j2)  # S-->P or P-->S
                print_inference_rule(inference_rule="Analogy")
                derived_sentences.append(derived_sentence)
            elif NALSyntax.Copula.is_symmetric(j1_copula) and not NALSyntax.Copula.is_symmetric(j2_copula):
                """
                # j1 = M<->S or S<->M
                # j2 = P-->M or M-->P
                # Swapped Analogy
                """
                derived_sentence = NALInferenceRules.Syllogistic.Analogy(j2, j1)  # S-->P or P-->S
                print_inference_rule(inference_rule="Swapped Analogy")
                derived_sentences.append(derived_sentence)
            elif NALSyntax.Copula.is_symmetric(j1_copula) and NALSyntax.Copula.is_symmetric(j2_copula):
                """
                # j1 = M<->P or P<->M
                # j2 = S<->M or M<->S
                # Resemblance
                """
                derived_sentence = NALInferenceRules.Syllogistic.Resemblance(j1, j2)  # S<->P
                print_inference_rule(inference_rule="Resemblance")
                derived_sentences.append(derived_sentence)
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
                j1_statement, j2_statement = j2_statement, j1_statement
                j1_subject_term, j2_subject_term = j2_subject_term, j1_subject_term
                j1_predicate_term, j2_predicate_term = j2_predicate_term, j1_predicate_term
                j1_copula, j2_copula = j2_copula, j1_copula
                swapped = True

            """
                j1 = S==>P or S<=>P
            """
            if NALSyntax.Copula.is_symmetric(j1_copula):
                """
                    j1 = S<=>P
                    j2 = S (A-->B)
                """
                derived_sentence = NALInferenceRules.Conditional.ConditionalAnalogy(j2, j1)  # P
                print_inference_rule(inference_rule="Conditional Analogy")
                derived_sentences.append(derived_sentence)
            else:
                """
                    j1 = S==>P
                    j2 = S or P (A-->B)
                """

                if j2_statement == j1_subject_term:
                    """
                        j2 = S
                    """
                    derived_sentence = NALInferenceRules.Conditional.ConditionalDeduction(j1, j2)  # P
                    print_inference_rule(inference_rule="Conditional Deduction")
                    derived_sentences.append(derived_sentence)
                elif j2_statement == j1_predicate_term:
                    """
                        j2 = P
                    """
                    derived_sentence = NALInferenceRules.Conditional.ConditionalAbduction(j1, j2)  # S
                    print_inference_rule(inference_rule="Conditional Abduction")
                    derived_sentences.append(derived_sentence)
                elif NALSyntax.TermConnector.is_conjunction(j1_subject_term.connector):
                    """
                        j1 = (C1 && C2 && ..CN && S) ==> P
                        j2 = S
                    """
                    derived_sentence = NALInferenceRules.Conditional.ConditionalConjunctionalDeduction(j1,j2)  # (C1 && C2 && ..CN) ==> P
                    print_inference_rule(inference_rule="Conditional Conjunctional Deduction")
                    derived_sentences.append(derived_sentence)

            if swapped:
                # restore sentences
                j1, j2 = j2, j1
                j1_statement, j2_statement = j2_statement, j1_statement
                j1_subject_term, j2_subject_term = j2_subject_term, j1_subject_term
                j1_predicate_term, j2_predicate_term = j2_predicate_term, j1_predicate_term
                j1_copula, j2_copula = j2_copula, j1_copula
                swapped = False



    elif isinstance(j1, NALGrammar.Goal):
        #todo conditional syllogism
        pass

    """
    ===============================================
    ===============================================
        Post-Processing
    ===============================================
    ===============================================
    """
    # mark sentences as interacted with each other
    j1.stamp.mutually_add_to_interacted_sentences(j2)

    return derived_sentences

def do_temporal_inference_two_premise(A: NALGrammar.Sentence, B: NALGrammar.Sentence) -> [NARSDataStructures.Task]:
    derived_sentences = []

    derived_sentence = NALInferenceRules.Conditional.ConditionalInduction(A, B) # A =|> B or A =/> B or B =/> A
    print_inference_rule(inference_rule="Temporal Induction")
    derived_sentences.append(derived_sentence)

    derived_sentence = NALInferenceRules.Conditional.ConditionalComparison(A, B) # A <|> B or  A </> B or B </> A
    print_inference_rule(inference_rule="Temporal Comparison")
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

    if isinstance(j, NALGrammar.Judgment):
        # Negation (--,(S-->P))
        derived_sentence = NALInferenceRules.Immediate.Negation(j)
        print_inference_rule(inference_rule="Negation")
        derived_sentences.append(derived_sentence)

        # Conversion (P --> S)
        if not j.stamp.from_one_premise_inference \
                and not NALSyntax.Copula.is_symmetric(j.statement.get_copula()) \
                and j.value.frequency > 0:
            derived_sentence = NALInferenceRules.Immediate.Conversion(j)
            print_inference_rule(inference_rule="Conversion")
            derived_sentences.append(derived_sentence)

        # Contraposition  ((--,P) ==> (--,S))
        if j.statement.get_copula() == NALSyntax.Copula.Implication and j.value.frequency < 1:
            derived_sentence = NALInferenceRules.Immediate.Contraposition(j)
            print_inference_rule(inference_rule="Contraposition")
            derived_sentences.append(derived_sentence)

        # Image
        if isinstance(j.statement.get_subject_term(), NALGrammar.CompoundTerm) \
            and j.statement.get_subject_term().connector == NALSyntax.TermConnector.Product:
            derived_sentence_array = NALInferenceRules.Immediate.ExtensionalImage(j)
            print_inference_rule(inference_rule="Extensional Image")
            for derived_sentence in derived_sentence_array:
                derived_sentences.append(derived_sentence)
        elif isinstance(j.statement.get_predicate_term(), NALGrammar.CompoundTerm) \
            and j.statement.get_predicate_term().connector == NALSyntax.TermConnector.Product:
            derived_sentence_array = NALInferenceRules.Immediate.IntensionalImage(j)
            print_inference_rule(inference_rule="Intensional Image")
            for derived_sentence in derived_sentence_array:
                derived_sentences.append(derived_sentence)

    return derived_sentences


def print_inference_rule(inference_rule="Inference"):
    if Global.Global.DEBUG: print(inference_rule)
