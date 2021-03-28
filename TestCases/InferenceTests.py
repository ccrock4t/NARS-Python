import multiprocessing
import sys
import threading

import InputBuffer
import NARS
from multiprocessing.queues import Queue
import NALGrammar
import NALInferenceRules

"""
    Author: Christian Hahm
    Created: March 23, 2021
    Purpose: Unit Testing for NARS inference.
        Tests the NARS' overall ability to perform inference, not simply the inference engine.
        This is not an exact science, since whether or not the tests pass depends not only the system's
        capability to do inference, but also whether its control mechanism selects the proper objects for inference
        within the allowed number of inference cycles.
"""


# This is a Queue that behaves like stdout
class StdoutQueue(Queue):
    def __init__(self,*args,**kwargs):
        super(StdoutQueue, self).__init__(*args,**kwargs,ctx=multiprocessing.get_context())

    def write(self,msg):
        self.put(msg)

    def flush(self):
        sys.__stdout__.flush()

def nars_process(input_judgment_q, input_question_q, output_q):
    testnars = NARS.NARS()
    sys.stdout = output_q

    # feed in judgments
    while input_judgment_q.qsize() > 0:
        InputBuffer.add_input_sentence(input_judgment_q.get())

    # process judgments
    testnars.do_working_cycles(50)

    # feed in questions
    while input_question_q.qsize() > 0:
        InputBuffer.add_input_sentence(input_question_q.get())

    # process questions
    testnars.do_working_cycles(100)

    sys.stdout = sys.__stdout__

def check_success(output_q: StdoutQueue, success_criteria: [str]):
    """

    :param output_q: Multi-process queue that holds the NARS' output
    :param success_criteria: array of strings that must be present in the output in order to be considered success
    :return: (True, None) if output passed all success_criteria
            (False, failed_criteria) if output failed a criterion
    """
    output = []
    while output_q.qsize() > 0:  # read and store result in log file
        output.append(output_q.get())

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

def initialize_multiprocess_queues():
    input_judgment_q = StdoutQueue()
    input_question_q = StdoutQueue()
    output_q = StdoutQueue()
    return input_judgment_q, input_question_q, output_q


def revision():
    """
        Test first-order deduction:
        j1: (S-->P). %1.0;0.9%
        j2: (S-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.81%
    """
    input_judgment_q, input_question_q, output_q = initialize_multiprocess_queues()

    j1 = NALGrammar.Sentence.new_sentence_from_string("(S-->P). %1.0;0.9%")
    j2 = NALGrammar.Sentence.new_sentence_from_string("(S-->P). %1.0;0.9%")
    input_judgment_q.put(j1)
    input_judgment_q.put(j2)
    input_question_q.put(NALGrammar.Sentence.new_sentence_from_string("(S-->P)?"))

    process = threading.Thread(target=nars_process, args=(input_judgment_q,input_question_q,output_q))
    process.start()
    process.join()

    success_criteria = []
    success_criteria.append(NALInferenceRules.nal_revision(j1, j2).get_formatted_string_no_id())

    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: Revision test failed: " + failed_criterion


def first_order_deduction():
    """
        Test first-order deduction:
        j1: (S-->M). %1.0;0.9%
        j2: (M-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.81%
    """
    input_judgment_q, input_question_q, output_q = initialize_multiprocess_queues()

    j1 = NALGrammar.Sentence.new_sentence_from_string("(M-->P). %1.0;0.9%")
    j2 = NALGrammar.Sentence.new_sentence_from_string("(S-->M). %1.0;0.9%")
    input_judgment_q.put(j1)
    input_judgment_q.put(j2)
    input_question_q.put(NALGrammar.Sentence.new_sentence_from_string("(S-->P)?"))

    process = threading.Thread(target=nars_process, args=(input_judgment_q,input_question_q,output_q))
    process.start()
    process.join()

    success_criteria = []
    success_criteria.append(NALInferenceRules.nal_deduction(j1, j2).get_formatted_string_no_id())

    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: First-order Deduction test failed: " + failed_criterion

def first_order_induction():
    """
        Test first-order induction:
        j1: (M-->S). %1.0;0.9%
        j2: (M-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.45%
           and
           (P-->S). %1.0;0.45%
    """
    input_judgment_q, input_question_q, output_q = initialize_multiprocess_queues()

    j1 = NALGrammar.Sentence.new_sentence_from_string("(M-->S). %1.0;0.9%")
    j2 = NALGrammar.Sentence.new_sentence_from_string("(M-->P). %1.0;0.9%")
    input_judgment_q.put(j1)
    input_judgment_q.put(j2)
    input_question_q.put(NALGrammar.Sentence.new_sentence_from_string("(S-->P)?"))
    input_question_q.put(NALGrammar.Sentence.new_sentence_from_string("(P-->S)?"))

    process = threading.Thread(target=nars_process, args=(input_judgment_q,input_question_q,output_q))
    process.start()
    process.join()

    success_criteria = []
    success_criteria.append(NALInferenceRules.nal_induction(j1, j2).get_formatted_string_no_id())
    success_criteria.append(NALInferenceRules.nal_induction(j2, j1).get_formatted_string_no_id())

    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: First-order Induction test failed: " + failed_criterion

def first_order_abduction():
    """
        Test first-order abduction:
        j1: (S-->M). %1.0;0.9%
        j2: (P-->M). %1.0;0.9%

        :- (S-->P). %1.0;0.45%
           and
           (P-->S). %1.0;0.45%
    """
    input_judgment_q, input_question_q, output_q = initialize_multiprocess_queues()

    j1 = NALGrammar.Sentence.new_sentence_from_string("(S-->M). %1.0;0.9%")
    j2 = NALGrammar.Sentence.new_sentence_from_string("(P-->M). %1.0;0.9%")
    input_judgment_q.put(j1)
    input_judgment_q.put(j2)
    input_question_q.put(NALGrammar.Sentence.new_sentence_from_string("(S-->P)?"))
    input_question_q.put(NALGrammar.Sentence.new_sentence_from_string("(P-->S)?"))

    process = threading.Thread(target=nars_process, args=(input_judgment_q,input_question_q,output_q))
    process.start()
    process.join()

    success_criteria = []
    success_criteria.append(NALInferenceRules.nal_abduction(j1, j2).get_formatted_string_no_id())
    success_criteria.append(NALInferenceRules.nal_abduction(j2, j1).get_formatted_string_no_id())

    success, failed_criterion = check_success(output_q, success_criteria)

    assert success,"TEST FAILURE: First-order Abduction test failed: " + failed_criterion

def main():
    revision()

    """
        First-Order syllogism tests
    """
    first_order_deduction()
    first_order_induction()
    first_order_abduction()

    print("All Inference Tests successfully passed.")

if __name__ == "__main__":
    main()