import NARSDataStructures
from NALGrammar import *
from NALSyntax import Punctuation
import NARS
from NARSMemory import Concept

"""
    Author: Christian Hahm
    Created: January 29, 2021
    Purpose: Defines NARS internal memory
"""

def test_table_removemax():
    """
        Test if the Table can successfully remove its maximum value
    """
    heap = NARSDataStructures.Table()
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    maximum = max(confidences)
    for c in confidences:
        sentence = Sentence(Statement(Term.make_term_from_string("a"), Term.make_term_from_string("b"), Copula.Inheritance),
                 TruthValue(0.9, c), Punctuation.Judgment)
        heap.insert(sentence)
    heapmax = heap.extract_max().value.confidence
    assert(heapmax == maximum), "TEST FAILURE: Heap did not properly retrieve maximum value"


def test_table_removemin():
    """
        Test if the Table can successfully remove its minimum value
    """
    heap = NARSDataStructures.Table()
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    minimum = min(confidences)
    for c in confidences:
        #make sentence <a --> b>. %0.9;c%
        sentence = Sentence(Statement(Term.make_term_from_string("a"), Term.make_term_from_string("b"), Copula.Inheritance),
                 TruthValue(0.9, c), Punctuation.Judgment)
        heap.insert(sentence)

    heapmin = heap.extract_min().value.confidence
    assert (heapmin == minimum), "TEST FAILURE: Heap did not properly retrieve minimum value"


def test_concept_termlinking():
    """
        Test if term links can be added and removed properly
    """
    testnars = NARS.NARS()
    statement_concept = testnars.memory.peek_concept(Term.make_term_from_string("(A-->B)"))
    conceptA = testnars.memory.peek_concept(Term.make_term_from_string("A"))
    conceptB = testnars.memory.peek_concept(Term.make_term_from_string("B"))

    assert (statement_concept.term_links.count == 2), "TEST FAILURE: Concept " + str(statement_concept) + " does not have 2 termlinks"
    assert (conceptA.term_links.count == 1), "TEST FAILURE: Concept " + str(conceptA) + " does not have 1 termlink"
    assert (conceptB.term_links.count == 1), "TEST FAILURE: Concept " + str(conceptB) + " does not have 1 termlink"

    statement_concept.remove_term_link(conceptA) # remove concept A's termlink

    assert (statement_concept.term_links.count == 1), "Concept " + str(statement_concept) + " does not have 1 termlink"
    assert (conceptA.term_links.count == 0), "TEST FAILURE: Concept " + str(conceptA) + " does not have 0 termlinks"
    assert (conceptB.term_links.count == 1), "TEST FAILURE: Concept " + str(conceptB) + " does not have 1 termlink"

    take = statement_concept.term_links.take().object # take out the only remaining concept (concept B)

    assert (take == conceptB), "TEST FAILURE: Removed concept was not Concept 'B'"
    assert (conceptB.term_links.count == 1), "TEST FAILURE: Concept does not have 1 termlink"


def test_bag_overflow():
    """
        Test if bag stays within capacity when it overflows.
    """
    testbag = NARSDataStructures.Bag(item_type=str)
    items_added = 0
    for i in range(0, NARS.Config.BAG_CAPACITY + 5):
        testbag.put_new_item(str(i))
        items_added = items_added + 1

    assert (items_added > NARS.Config.BAG_CAPACITY), "TEST FAILURE: For this test, add more items than the capacity"
    assert (testbag.count == NARS.Config.BAG_CAPACITY), "TEST FAILURE: Bag did not maintain capacity on overflow"


if __name__ == "__main__":
    """
        Table Tests
    """
    test_table_removemax()
    test_table_removemin()

    """
        Concept Tests
    """
    test_concept_termlinking()

    """
        Bag Tests
    """
    test_bag_overflow()

    print("All tests successfully passed.")