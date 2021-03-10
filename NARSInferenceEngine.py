"""
    Author: Christian Hahm
    Created: March 8, 2021
    Purpose: Identifies and performs inference on a task and belief.
"""
from Global import GlobalGUI
from NALGrammar import assert_sentence, Sentence, Copula
from NALInferenceRules import nal_deduction, nal_revision, nal_induction, nal_abduction, nal_comparison, nal_analogy
from NARSDataStructures import assert_task, Task


def perform_inference(t1: Task, j2: Sentence) -> [Task]:
    """
        Derives a new task by performing the appropriate inference rules on the given Task and belief.
        The resultant sentence's evidential base is appropriately merged from its parents.
        Also marks the Task t1 as having interacted with belief j2.

        :param t1: Task containing sentence j1
        :param j2: Belief containing sentence j2

        :assumes j1 and j2 have distinct evidential bases B1 and B2: B1 ⋂ B2 = Ø
                (no evidential overlap)

        :returns An array of the derived Tasks, or None if the inputs have evidential overlap
    """
    assert_task(t1)
    assert_sentence(j2)

    derived_tasks = []
    j1 = t1.sentence

    # Identify and perform inference
    j1_term = j1.statement.term
    j2_term = j2.statement.term
    j1_subject_term = j1.statement.term.get_subject_term()
    j2_subject_term = j2.statement.term.get_subject_term()
    j1_predicate_term = j1.statement.term.get_predicate_term()
    j2_predicate_term = j2.statement.term.get_predicate_term()
    j1_copula = j1.statement.copula
    j2_copula = j2.statement.copula

    if j1_subject_term == j2_predicate_term and j2_subject_term == j1_predicate_term:
        # S-->P, P-->S
        # S<->P, P<->S
        return  # don't do inference, it will result in tautology

    if j1_copula == Copula.Inheritance and j2_copula == Copula.Inheritance:
        if j1_term == j2_term:
            # revision
            # j1=S-->P, j2=S-->P
            derived_sentence = nal_revision(j1, j2) # S-->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Revision")
            if derived_task is not None: derived_tasks.append(derived_task)
        elif j1_subject_term == j2_predicate_term:
            # deduction
            # j1=M-->P, j2=S-->M
            derived_sentence = nal_deduction(j1, j2)
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Deduction")
            if derived_task is not None: derived_tasks.append(derived_task)
        elif j1_predicate_term == j2_subject_term:
            # deduction
            # j1=S-->M, j2=M-->P
            derived_sentence = nal_deduction(j2, j1)  # S-->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Deduction")
            if derived_task is not None: derived_tasks.append(derived_task)
        elif j1_subject_term  == j2_subject_term:
            # induction
            # j1=M-->P, j2=M-->S
            derived_sentence = nal_induction(j1, j2)  # S-->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Induction")
            if derived_task is not None: derived_tasks.append(derived_task)

            # also treat them conversely, as j1=M-->S and j2=M-->P
            derived_sentence = nal_induction(j2, j1)  # S-->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Induction")
            if derived_task is not None: derived_tasks.append(derived_task)

            # comparison
            # j1=M-->P, j2=M-->S
            derived_sentence = nal_comparison(j1,j2)  # S<->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Comparison")
            if derived_task is not None: derived_tasks.append(derived_task)
        elif j1_predicate_term == j2_predicate_term:
            # abduction
            # j1=P -->M, j2=S-->M
            derived_sentence = nal_abduction(j1, j2)  # S-->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Abduction")
            if derived_task is not None: derived_tasks.append(derived_task)

            # also process them conversely, where j1=S-->M and j2=P-->M
            derived_sentence = nal_abduction(j2, j1)  # S-->P
            derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Abduction")
            if derived_task is not None: derived_tasks.append(derived_task)
        else:
            assert False, "error, concept " + str(j1.statement.term) + " and " + str(j2.statement.term) + " not related"
    elif (j1_copula == Copula.Inheritance and j2_copula == Copula.Similarity) or (j1_copula == Copula.Similarity and j2_copula == Copula.Inheritance):
        # analogy
        if j1_copula == Copula.Inheritance:
            # j1=M-->P, j2=S<->M or j1=M-->P, j2=M<->S
            derived_sentence = nal_analogy(j1, j2)  # S-->P
        else:
            # j1=S<->M, j2=M-->P or j1=M<->S, j2=M-->P
            derived_sentence = nal_analogy(j2, j1)  # S-->P

        derived_task = make_new_task_from_derived_sentence(derived_sentence, j1, j2, inference_rule="Comparison")
        if derived_task is not None: derived_tasks.append(derived_task)

    # mark task as interacted with belief
    t1.interacted_beliefs.append(j2)  # mark task t1 as interacted with belief j2

    return derived_tasks


def make_new_task_from_derived_sentence(derived_sentence: Sentence, j1: Sentence, j2: Sentence, inference_rule="Inference"):
    """
            Makes a new task from a derived sentence.
            Returns None for Tautologies.

    :param inference_rule: String, name of inference rule from which sentence was derived
    :param j1: Parent Sentence 1
    :param j2: Parent Sentence 2
    :param derived_sentence:  Sentence derived from j1 and j2
    :return: Task for derived_sentence
    """
    # merge in the parent sentence's evidential bases
    derived_sentence.stamp.evidential_base.merge_evidential_base_into_self(j1.stamp.evidential_base)
    derived_sentence.stamp.evidential_base.merge_evidential_base_into_self(j2.stamp.evidential_base)

    derived_task = Task(derived_sentence)
    if GlobalGUI.gui_use_interface:
        print(inference_rule + " derived new Task: " + str(derived_task) + " from " + j1.get_formatted_string() + " and " + j2.get_formatted_string())
        print("Derived with evidential base " + str(derived_sentence.stamp.evidential_base.base))
    return derived_task
