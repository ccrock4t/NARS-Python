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
    heap = NARSDataStructures.Table()
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    maximum = max(confidences)
    for c in confidences:
        sentence = Sentence(Statement(Term.make_term_from_string("a"), Term.make_term_from_string("b"), Copula.Inheritance),
                 TruthValue(0.9, c), Punctuation.Judgment)
        heap.insert(sentence)
    heapmax = heap.extract_max().value.confidence
    assert(heapmax == maximum), "Heap did not properly retrieve maximum value"


def test_table_removemin():
    heap = NARSDataStructures.Table()
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    minimum = min(confidences)
    for c in confidences:
        #make sentence <a --> b>. %0.9;c%
        sentence = Sentence(Statement(Term.make_term_from_string("a"), Term.make_term_from_string("b"), Copula.Inheritance),
                 TruthValue(0.9, c), Punctuation.Judgment)
        heap.insert(sentence)

    heapmin = heap.extract_min().value.confidence
    assert (heapmin == minimum), "Heap did not properly retrieve minimum value"

def test_concept_termlinking():
    testnars = NARS.NARS()
    statement_concept = testnars.memory.get_concept(Term.make_term_from_string("(A-->B)"))
    conceptA = testnars.memory.get_concept(Term.make_term_from_string("A"))
    conceptB = testnars.memory.get_concept(Term.make_term_from_string("B"))

    assert (statement_concept.term_links.count == 2), "Concept " + str(statement_concept) + " does not have 2 termlinks"
    assert (conceptA.term_links.count == 1), "Concept " + str(conceptA) + " does not have 1 termlink"
    assert (conceptB.term_links.count == 1), "Concept " + str(conceptB) + " does not have 1 termlink"

    statement_concept.remove_term_link(conceptA) # remove concept A's termlink

    assert (statement_concept.term_links.count == 1), "Concept " + str(statement_concept) + " does not have 1 termlink"
    assert (conceptA.term_links.count == 0), "Concept " + str(conceptA) + " does not have 0 termlinks"
    assert (conceptB.term_links.count == 1), "Concept " + str(conceptB) + " does not have 1 termlink"

    take = statement_concept.term_links.take().object # take out the only remaining concept (concept B)

    assert (take == conceptB), "Removed concept was not Concept 'B'"
    assert (conceptB.term_links.count == 1), "Concept does not have 1 termlink"

if __name__ == "__main__":
    """
        MaxHeap Tests
    """
    test_table_removemax()
    test_table_removemin()
    test_concept_termlinking()
    print("Everything passed")