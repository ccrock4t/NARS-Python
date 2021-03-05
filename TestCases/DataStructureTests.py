import NARSDataStructures
from NALGrammar import *
from NALSyntax import Punctuation


def test_table_removemax():
    heap = NARSDataStructures.Table()
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    maximum = max(confidences)
    for c in confidences:
        sentence = Sentence(Statement(Term.make_term_from_string("a"), Term.make_term_from_string("b"), Copula.Inheritance),
                 TruthValue(0.9, c), Punctuation.Judgment)
        heap.insert(sentence)
    heapmax = heap.extract_max().value.confidence
    print(heapmax)
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
    print(heapmin)
    assert (heapmin == minimum), "Heap did not properly retrieve minimum value"


if __name__ == "__main__":
    """
        MaxHeap Tests
    """
    test_table_removemax()
    test_table_removemin()
    print("Everything passed")