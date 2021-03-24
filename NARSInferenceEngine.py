"""
    Author: Christian Hahm
    Created: March 8, 2021
    Purpose: Identifies and performs inference on 2 related sentences
"""
from Global import GlobalGUI
from NALGrammar import assert_sentence, Sentence, Copula, Question, Punctuation
from NALInferenceRules import nal_deduction, nal_revision, nal_induction, nal_abduction, nal_comparison, nal_analogy, \
    nal_exemplification, nal_resemblance, nal_conversion
from NARSDataStructures import assert_task, Task


def do_inference(j1: Sentence, j2: Sentence) -> [Task]:
    """
        Derives a new task by performing the appropriate inference rules on the given semantically related sentences.
        The resultant sentence's evidential base is merged from its parents.

        :param t1: Task containing sentence j1
        :param j2: Belief containing sentence j2

        :assume j1 and j2 have distinct evidential bases B1 and B2: B1 ⋂ B2 = Ø
                (no evidential overlap)

        :returns An array of the derived Tasks, or None if the inputs have evidential overlap
    """
    assert_sentence(j1)
    assert_sentence(j2)

    """
    ===============================================
    ===============================================
        Pre-Processing
    ===============================================
    ===============================================
    """
    derived_tasks = []

    j1_term = j1.statement.term
    j2_term = j2.statement.term
    j1_subject_term = j1.statement.get_subject_term()
    j2_subject_term = j2.statement.get_subject_term()
    j1_predicate_term = j1.statement.get_predicate_term()
    j2_predicate_term = j2.statement.get_predicate_term()
    j1_copula = j1.statement.copula
    j2_copula = j2.statement.copula

    # need to check check for tautology if 1 of the copulas is not symmetric
    # Catches (S-->P,P<->S) and (S-->P, P-->S) and (P-->S,S<->P) and (P-->S, S-->P)
    tautology = (not Copula.is_symmetric(j1_copula) or not Copula.is_symmetric(j2_copula)) and \
                (j1_subject_term == j2_predicate_term and j1_predicate_term == j2_subject_term) #

    # Catches (S-->P,S<->P) and (S<->P,S-->P)
    tautology = tautology or \
                ((not Copula.is_symmetric(j1_copula) and Copula.is_symmetric(j2_copula)) or \
                (Copula.is_symmetric(j1_copula) and not Copula.is_symmetric(j2_copula))) and \
                (j1_subject_term == j2_subject_term and j1_predicate_term == j2_predicate_term)

    if tautology:
        return derived_tasks  # don't do inference, it will result in tautology

    is_question = isinstance(j1, Question) or isinstance(j2, Question)

    """
    ===============================================
    ===============================================
        First-order and Higher-Order Syllogistic Rules
    ===============================================
    ===============================================
    """

    if j1_term == j2_term:
        """
        # Revision
        # j1=S-->P, j2=S-->P
        # or j1=S<->P, j2=S<->P or P<->S
        """
        if is_question: return # can't do revision with questions

        derived_sentence = nal_revision(j1, j2)  # S-->P
        derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Revision")
        derived_tasks.append(derived_task)
    elif not Copula.is_symmetric(j1_copula) and not Copula.is_symmetric(j2_copula):
        if j1_subject_term == j2_predicate_term or j1_predicate_term == j2_subject_term:
            """
            # j1=M-->P, j2=S-->M
            # or j1=M-->S, j2=P-->M
            # OR
            # j1=S-->M, j2=M-->P
            # or j1=P-->M, j2=M-->S
            """
            swapped = False
            if j1_subject_term != j2_predicate_term:
                # j1=S-->M, j2=M-->P
                # or j1=P-->M, j2=M-->S
                j1, j2 = j2, j1  # swap sentences
                swapped = True
            # deduction
            derived_sentence = nal_deduction(j1, j2)  # S-->P or P-->S
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Deduction")
            derived_tasks.append(derived_task)

            """
            # Swapped Exemplification
            """
            derived_sentence = nal_exemplification(j2, j1)  # P-->S or S-->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2,
                                                               inference_rule="Swapped Exemplification")
            derived_tasks.append(derived_task)

            if swapped:
                j1, j2 = j2, j1  # restore sentences
                swapped = False
        elif j1_subject_term == j2_subject_term:
            """
            # j1=M-->P, j2=M-->S
            # Induction
            """
            derived_sentence = nal_induction(j1, j2)  # S-->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Induction")
            derived_tasks.append(derived_task)

            """
            # Swapped Induction
            """
            derived_sentence = nal_induction(j2, j1)  # P-->S
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2,
                                                               inference_rule="Swapped Induction")
            derived_tasks.append(derived_task)

            # comparison
            derived_sentence = nal_comparison(j1, j2)  # S<->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Comparison")
            derived_tasks.append(derived_task)
        elif j1_predicate_term == j2_predicate_term:
            """
            # j1=P-->M, j2=S-->M
            # Abduction
            """
            derived_sentence = nal_abduction(j1, j2)  # S-->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Abduction")
            derived_tasks.append(derived_task)

            """
            # Swapped Abduction
            """
            derived_sentence = nal_abduction(j2, j1)  # P-->S
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2,
                                                               inference_rule="Swapped Abduction")
            derived_tasks.append(derived_task)

            # comparison
            derived_sentence = nal_comparison(j1, j2)  # S<->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Comparison")
            derived_tasks.append(derived_task)
        else:
            assert False, "error, concept " + str(j1.statement.term) + " and " + str(j2.statement.term) + " not related"
    elif not Copula.is_symmetric(j1_copula) and Copula.is_symmetric(j2_copula):
        """
        # j1=M-->P or P-->M
        # j2=S<->M or M<->S
        # Analogy
        """

        derived_sentence = nal_analogy(j1, j2)  # S-->P or P-->S
        derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Analogy")
        derived_tasks.append(derived_task)
    elif Copula.is_symmetric(j1_copula) and not Copula.is_symmetric(j2_copula):
        """
        # j1=M<->P or P<->M
        # j2=S-->M or M-->S
        # Swapped Analogy
        """
        derived_sentence = nal_analogy(j2, j1)  # S-->P or P-->S
        derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Swapped Analogy")
        derived_tasks.append(derived_task)
    elif Copula.is_symmetric(j1_copula) and Copula.is_symmetric(j2_copula):
        """
        # j1=M<->P or P<->M
        # j2=S<->M or M<->S
        # Resemblance
        """
        derived_sentence = nal_resemblance(j1, j2)  # S<->P
        derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Resemblance")
        derived_tasks.append(derived_task)

    """
    ===============================================
    ===============================================
        Post-Processing
    ===============================================
    ===============================================
    """
    # mark task as interacted with sentnece
    j1.stamp.mutually_add_to_interacted_sentences(j2)

    conversion_tasks_to_append = []
    for derived_task in derived_tasks:
        """
            # apply the Conversion rule on all inheritance statements
        """
        if derived_task.sentence.statement.copula == Copula.Inheritance:
            derived_sentence = nal_conversion(derived_task.sentence)
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1=derived_task.sentence, j2=None, inference_rule="Conversion")
            conversion_tasks_to_append.append(derived_task)

    for conversion_task in conversion_tasks_to_append:
        derived_tasks.append(conversion_task)

    return derived_tasks


def make_new_task_from_derived_sentence(derived_sentence: Sentence, j1: Sentence, j2: Sentence,
                                        inference_rule="Inference"):
    """
            Makes a new task from a derived sentence.
            Returns None for Tautologies.

    :param derived_sentence:  Sentence derived from j1 and j2
    :param j1: Parent Sentence 1
    :param j2: Parent Sentence 2 - can be None
    :param inference_rule: String, name of inference rule from which sentence was derived

    :return: Task for derived_sentence
    """
    #print(inference_rule + " Derived Task: " + str(derived_sentence) + " using j1: " + str(j1) + " j2: " + str(j2))
    derived_task = Task(derived_sentence)
    return derived_task
