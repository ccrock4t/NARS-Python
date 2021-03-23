import multiprocessing
import os
import sys
import threading

import InputBuffer
import NARS
from multiprocessing import Process
from multiprocessing.queues import Queue

from NALGrammar import Term, TruthValue, Sentence, Statement
from NALSyntax import Punctuation

"""
    Author: Christian Hahm
    Created: March 23, 2021
    Purpose: Unit Testing for NARS inference.
    Tests the overall NARS ability to perform inference, not simply the inference engine.
    This is not an exact science, since whether or not the tests pass depends not only the system's
    capability to do inference, but also whether its control mechanism selects the proper objects for inference.
"""
# This is a Queue that behaves like stdout
class StdoutQueue(Queue):
    def __init__(self,*args,**kwargs):
        super(StdoutQueue, self).__init__(*args,**kwargs,ctx=multiprocessing.get_context())

    def write(self,msg):
        self.put(msg)

    def flush(self):
        sys.__stdout__.flush()


def first_order_deduction():
    """
        Test first-order deduction:
        j1: (S-->M). %1.0;0.9%
        j2: (M-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.81%
    """
    q = StdoutQueue()

    def nars_process(q):
        testnars = NARS.NARS()
        sys.stdout = q
        InputBuffer.add_input("(S-->M). %1.0;0.9%")
        InputBuffer.add_input("(M-->P). %1.0;0.9%")
        InputBuffer.add_input("(S-->P)?")
        testnars.do_working_cycles(50)
        sys.stdout = sys.__stdout__

    process = threading.Thread(target=nars_process, args=(q,))
    process.start()
    process.join()


    success_criteria = []
    success_criteria.append(InputBuffer.parse_sentence("(S-->P). %1.0;0.81%").get_formatted_string_no_id())

    output = []
    while q.qsize() > 0:  # read and store result in log file
        output.append(q.get())

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
    q = StdoutQueue()

    def nars_process(q):
        testnars = NARS.NARS()
        sys.stdout = q
        InputBuffer.add_input("(M-->S). %1.0;0.9%")
        InputBuffer.add_input("(M-->P). %1.0;0.9%")
        InputBuffer.add_input("(S-->P)?")
        InputBuffer.add_input("(P-->S)?")
        testnars.do_working_cycles(50)
        sys.stdout = sys.__stdout__

    process = threading.Thread(target=nars_process, args=(q,))
    process.start()
    process.join()

    success_criteria = []
    success_criteria.append(InputBuffer.parse_sentence("(S-->P). %1.0;0.45%").get_formatted_string_no_id())
    success_criteria.append(InputBuffer.parse_sentence("(P-->S). %1.0;0.45%").get_formatted_string_no_id())

    output = []
    while q.qsize() > 0:  # read and store result in log file
        output.append(q.get())

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
    q = StdoutQueue()

    def nars_process(q):
        testnars = NARS.NARS()
        sys.stdout = q
        InputBuffer.add_input("(S-->M). %1.0;0.9%")
        InputBuffer.add_input("(P-->M). %1.0;0.9%")
        InputBuffer.add_input("(S-->P)?")
        InputBuffer.add_input("(P-->S)?")
        testnars.do_working_cycles(50)
        sys.stdout = sys.__stdout__

    process = threading.Thread(target=nars_process, args=(q,))
    process.start()
    process.join()

    success_criteria = []
    success_criteria.append(InputBuffer.parse_sentence("(S-->P). %1.0;0.45%").get_formatted_string_no_id())
    success_criteria.append(InputBuffer.parse_sentence("(P-->S). %1.0;0.45%").get_formatted_string_no_id())

    output = []
    while q.qsize() > 0:  # read and store result in log file
        output.append(q.get())

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

    assert success,"TEST FAILURE: First-order Abduction test failed: " + failed_criterion


if __name__ == "__main__":
    """
        First-Order syllogism tests
    """
    first_order_deduction()
    first_order_induction()
    first_order_abduction()

    print("All tests successfully passed.")