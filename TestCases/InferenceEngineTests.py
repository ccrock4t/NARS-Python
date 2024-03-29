import threading
import InputChannel

import NALGrammar
import NALInferenceRules.Local
import NALInferenceRules.Conditional

import NARSInferenceEngine

"""
    Author: Christian Hahm
    Created: March 23, 2021
    Purpose: Unit Testing for the Narsese Inference Engine.
        Tests if the inference engine returns all expected inference results for the given premises.
"""


def run_test(j1, j2=None):
    """
        Runs j1 and j2 through the inference engine.
        Returns an array of the outputs.
    :param j1:
    :param j2:
    :return:
    """
    # feed judgments into the engine
    output = None
    if j2 is not None:
        output = NARSInferenceEngine.do_semantic_inference_two_premise(j1, j2)
    else:
        output = NARSInferenceEngine.do_inference_one_premise(j1)
    return output


def check_success(output_q: [], success_criteria: [str]):
    """

    :param output_q: queue holding inference engine output tasts
    :param success_criteria: array of strings that must be present in the output in order to be considered success
    :return: (True, None) if output passed all success_criteria
            (False, failed_criteria) if output failed a criterion
    """
    output = []
    while len(output_q) > 0:  # read and store result in log file
        output.append(output_q.pop().get_term_string_no_id())

    success = True
    failed_criterion = ""
    for criterion in success_criteria:
        success = False
        for line in output:
            if criterion in line:
                success = True
                break
        if not success:
            failed_criterion = criterion
            break

    return success, failed_criterion


def revision():
    """
        Test first-order deduction:
        j1: (S-->P). %1.0;0.9%
        j2: (S-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(S-->P). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(S-->P). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Local.Revision(j1, j2).get_term_string_no_id())

    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: Revision test failed: " + failed_criterion


def first_order_deduction():
    """
        Test first-order deduction:
        j1: (S-->M). %1.0;0.9%
        j2: (M-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(M-->P). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(S-->M). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Syllogistic.Deduction(j1, j2).get_term_string_no_id())

    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: First-order Deduction test failed: " + failed_criterion

def first_order_induction():
    """
        Test first-order induction:
        j1: (M-->S). %1.0;0.9%
        j2: (M-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.45%
        :- (P-->S). %1.0;0.45%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(M-->S). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(M-->P). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Syllogistic.Induction(j1, j2).get_term_string_no_id())
    success_criteria.append(NALInferenceRules.Syllogistic.Induction(j2, j1).get_term_string_no_id())

    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: First-order Induction test failed: " + failed_criterion

def first_order_abduction():
    """
        Test first-order abduction:
        j1: (S-->M). %1.0;0.9%
        j2: (P-->M). %1.0;0.9%

        :- (S-->P). %1.0;0.45%
        :- (P-->S). %1.0;0.45%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(S-->M). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(P-->M). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Syllogistic.Abduction(j1, j2).get_term_string_no_id())
    success_criteria.append(NALInferenceRules.Syllogistic.Abduction(j2, j1).get_term_string_no_id())

    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: First-order Abduction test failed: " + failed_criterion

def first_order_analogy():
    """
        Test first-order analogy:
        j1: (chimp-->monkey). %1.0;0.9%
        j2: (human<->monkey). %1.0;0.9%

        :- (chimp-->human). %1.0;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(chimp-->monkey). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(human<->monkey). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Syllogistic.Analogy(j1, j2).get_term_string_no_id())

    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: First-order Analogy test failed: " + failed_criterion

def first_order_intensional_composition():
    """
        Test Intensional Composition rules:
        j1: (M --> S). %1.0;0.9%
        j2: (M --> P). %1.0;0.9%

        :- (M --> (S | P)).
        :- (M --> (S & P)).
        :- (M --> (S - P)).
        :- (M --> (P - S)).
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(M-->S). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(M-->P). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Composition.ConjunctionOrExtensionalIntersection(j1, j2).get_term_string_no_id())
    success_criteria.append(NALInferenceRules.Composition.DisjunctionOrIntensionalIntersection(j1, j2).get_term_string_no_id())
    success_criteria.append(NALInferenceRules.Composition.ExtensionalDifference(j1, j2).get_term_string_no_id())
    success_criteria.append(NALInferenceRules.Composition.ExtensionalDifference(j2, j1).get_term_string_no_id())

    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: Intensional Composition test failed: " + failed_criterion

def first_order_extensional_composition():
    """
        Test Extensional Composition rules:
        j1: (S-->M). %1.0;0.9%
        j2: (P-->M). %1.0;0.9%

        :- ((S | P) --> M).
        :- ((S & P) --> M).
        :- ((S ~ P) --> M).
        :- ((P ~ S) --> M).
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(S-->M). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(P-->M). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Composition.ConjunctionOrExtensionalIntersection(j1, j2).get_term_string_no_id())
    success_criteria.append(NALInferenceRules.Composition.DisjunctionOrIntensionalIntersection(j1, j2).get_term_string_no_id())
    success_criteria.append(NALInferenceRules.Composition.IntensionalDifference(j1, j2).get_term_string_no_id())
    success_criteria.append(NALInferenceRules.Composition.IntensionalDifference(j2, j1).get_term_string_no_id())
    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: Extensional Composition test failed: " + failed_criterion

def first_order_exemplification():
    """
        Test Extensional Composition rules:
        j1: (S-->M). %1.0;0.9%
        j2: (P-->M). %1.0;0.9%

        :- ((S | P) --> M).
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(P-->M). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(M-->S). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Syllogistic.Exemplification(j1, j2).get_term_string_no_id())
    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: Exemplification test failed: " + failed_criterion


def extensional_image():
    """
        Test Extensional Image rule:
        j: ((*,S,P)-->R). %1.0;0.9%

        :- j: (S-->(/,R,_,P)). %1.0;0.9%
        :- j: (P-->(/,R,S,_)). %1.0;0.9%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("((*,S,P)-->R). %1.0;0.9%")

    output_q = run_test(j1)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Immediate.ExtensionalImage(j1).get_term_string_no_id())
    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: Extensional Image test failed: " + failed_criterion

def conditional_analogy():
    """
        Test Conditional Analogy rule:
        j1: S<=>P %1.0;0.9%
        j2: S %1.0;0.9%

        :- P %1.0;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(a-->b). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("((a-->b)<=>(c-->d)). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Conditional.ConditionalAnalogy(j1, j2).get_term_string_no_id())
    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: Conditional Analogy test failed: " + failed_criterion

def conditional_deduction():
    """
        Test Conditional Deduction rule:
        j1: S==>P %1.0;0.9%
        j2: S %1.0;0.9%

        :- P %1.0;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("((a-->b)==>(c-->d)). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(a-->b). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Conditional.ConditionalJudgmentDeduction(j1, j2).get_term_string_no_id())
    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: Conditional Deduction test failed: " + failed_criterion

def conditional_abduction():
    """
        Test Conditional Abduction rule:
        j1: S==>P %1.0;0.9%
        j2: P %1.0;0.9%

        :- S %1.0;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("((a-->b)==>(c-->d)). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(c-->d). %1.0;0.9%")

    output_q = run_test(j1,j2)

    success_criteria = []
    success_criteria.append(NALInferenceRules.Conditional.ConditionalJudgmentAbduction(j1, j2).get_term_string_no_id())
    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: Conditional Abduction test failed: " + failed_criterion

def conditional_conjunctional_deduction():
    """
        Test Conditional Conjunctional Deduction rule:
        j1: (C1 && C2 && ... CN && S) ==> P %1.0;0.9%
        j2: S %1.0;0.9%

        :- (C1 && C2 && ... CN) ==> P %1.0;0.81%
    """

    # test removal of second element
    j1 = NALGrammar.Sentences.new_sentence_from_string("((&&,(a-->b),(c-->d))==>(e-->f)). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(c-->d). %1.0;0.9%")
    output_q = run_test(j1, j2)

    success_criteria = []
    success_criteria.append(
        NALInferenceRules.Conditional.ConditionalConjunctionalDeduction(j1, j2).get_term_string_no_id())
    success, failed_criterion = check_success(output_q, success_criteria)

    assert success, "TEST FAILURE: Conditional Conjunctional Deduction test failed: " + failed_criterion

def conditional_conjunctional_abduction():
    """
        Test Conditional Conjunctional Deduction rule:
        j1: (C1 && C2 && ... CN && S) ==> P %1.0;0.9%
        j2: (C1 && C2 && ... CN) ==> P %1.0;0.9%

        :- S %1.0;0.45%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("((&&,(a-->b),(c-->d))==>(e-->f)). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("((c-->d)==>(e-->f)). %1.0;0.9%")
    output_q = run_test(j1, j2)

    success_criteria = []
    success_criteria.append(
        NALInferenceRules.Conditional.ConditionalConjunctionalAbduction(j1, j2).get_term_string_no_id())
    success, failed_criterion = check_success(output_q, success_criteria)

    assert success, "TEST FAILURE: Conditional Conjunctional Abduction test failed: " + failed_criterion

def main():
    revision()

    """
        First-Order syllogism tests
    """
    first_order_abduction()
    first_order_analogy()
    first_order_deduction()
    first_order_induction()
    first_order_exemplification()

    """
        Composition
    """
    first_order_extensional_composition()
    first_order_intensional_composition()

    """
        Conditional Syllogism
    """
    # conditional_abduction()
    # conditional_analogy()
    # conditional_deduction()
    # conditional_conjunctional_deduction()
    # conditional_conjunctional_abduction()

    print("All Inference Engine Tests successfully passed.")

if __name__ == "__main__":
    main()