import NARSDataStructures
import NALGrammar
import NALSyntax
import NARS
import NARSMemory

"""
    Author: Christian Hahm
    Created: January 29, 2021
    Purpose: Unit Testing for NARS data structures
"""

def test_table_removemax():
    """
        Test if the Table can successfully remove its maximum value
    """
    table = NARSDataStructures.Table()
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    maximum = max(confidences)
    for c in confidences:
        sentence = NALGrammar.Judgment(
            NALGrammar.Statement(NALGrammar.Term.get_term_from_string("a"), NALGrammar.Term.get_term_from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.TruthValue(0.9, c))
        table.put(sentence)
    tablemax = table.extract_max().value.confidence
    assert(tablemax == maximum), "TEST FAILURE: Table did not properly retrieve maximum value"


def test_table_removemin():
    """
        Test if the Table can successfully remove its minimum value
    """
    table = NARSDataStructures.Table()
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    minimum = min(confidences)
    for c in confidences:
        #make sentence <a --> b>. %0.9;c%
        sentence = NALGrammar.Judgment(
            NALGrammar.Statement(NALGrammar.Term.get_term_from_string("a"), NALGrammar.Term.get_term_from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.TruthValue(0.9, c))
        table.put(sentence)

    tablemin = table.extract_min().value.confidence
    assert (tablemin == minimum), "TEST FAILURE: Table did not properly retrieve minimum value"

def test_buffer_removemax():
    """
        Test if the Table can successfully remove its maximum value
    """
    buffer = NARSDataStructures.Buffer(NALGrammar.Sentence)
    priorities = [0.6, 0.2, 0.99, 0.5, 0.9]
    maximum = max(priorities)
    for p in priorities:
        sentence = NALGrammar.Judgment(
            NALGrammar.Statement(NALGrammar.Term.get_term_from_string("a"), NALGrammar.Term.get_term_from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.TruthValue(0.9, 0.9))
        item = NARSDataStructures.ItemContainer.Item(sentence,-1,0.99)
        item.budget.priority = p
        buffer.put(item)
    buffermax = buffer.extract_max().budget.priority
    assert(buffermax == maximum), "TEST FAILURE: Buffer did not properly retrieve maximum value"


def test_buffer_removemin():
    """
        Test if the Table can successfully remove its minimum value
    """
    buffer = NARSDataStructures.Buffer(NALGrammar.Sentence)
    priorities = [0.6, 0.2, 0.99, 0.5, 0.9]
    minimum = min(priorities)
    for p in priorities:
        #make sentence <a --> b>. %0.9;c%
        sentence = NALGrammar.Judgment(
            NALGrammar.Statement(NALGrammar.Term.get_term_from_string("a"), NALGrammar.Term.get_term_from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.TruthValue(0.9, 0.9))
        item = NARSDataStructures.ItemContainer.Item(sentence,-1,0.99)
        item.budget.priority = p
        buffer.put(item)

    buffermin = buffer.extract_min().budget.priority
    assert (buffermin == minimum), "TEST FAILURE: Buffer did not properly retrieve minimum value"



def test_concept_termlinking():
    """
        Test if term links can be added and removed properly from a concept
    """
    memory = NARSMemory.Memory()
    statement_concept = memory.peek_concept(NALGrammar.Term.get_term_from_string("(A-->B)"))
    conceptA = memory.peek_concept(NALGrammar.Term.get_term_from_string("A"))
    conceptB = memory.peek_concept(NALGrammar.Term.get_term_from_string("B"))

    assert (statement_concept.term_links.count == 2), "TEST FAILURE: Concept " + str(statement_concept) + " does not have 2 termlinks"
    assert (conceptA.term_links.count == 1), "TEST FAILURE: Concept " + str(conceptA) + " does not have 1 termlink. Has: " + str(conceptA.term_links.count)
    assert (conceptB.term_links.count == 1), "TEST FAILURE: Concept " + str(conceptB) + " does not have 1 termlink. Has: " + str(conceptB.term_links.count)

    statement_concept.remove_term_link(conceptA) # remove concept A's termlink

    assert (statement_concept.term_links.count == 1), "Concept " + str(statement_concept) + " does not have 1 termlink"
    assert (conceptA.term_links.count == 0), "TEST FAILURE: Concept " + str(conceptA) + " does not have 0 termlinks"
    assert (conceptB.term_links.count == 1), "TEST FAILURE: Concept " + str(conceptB) + " does not have 1 termlink"

    take = statement_concept.term_links.temporary_take().object # take out the only remaining concept (concept B)

    assert (take == conceptB), "TEST FAILURE: Removed concept was not Concept 'B'"
    assert (conceptB.term_links.count == 1), "TEST FAILURE: Concept does not have 1 termlink"


def test_bag_overflow_purge():
    """
        Test if bag stays within capacity when it overflows.
    """
    testbag = NARSDataStructures.Bag(item_type=NALGrammar.Sentence)
    items_added = 0
    for i in range(0, NARS.Config.BAG_DEFAULT_CAPACITY + 5):
        testbag.put(NALGrammar.Sentence.new_sentence_from_string("(a-->b)."))
        items_added = items_added + 1
        if items_added <= NARS.Config.BAG_DEFAULT_CAPACITY:
            assert len(testbag) == items_added,"TEST FAILURE: Length of bag does not equal # of items added"

    assert (items_added > NARS.Config.BAG_DEFAULT_CAPACITY), "TEST FAILURE: For this test, add more items than the capacity"
    assert (testbag.count == NARS.Config.BAG_DEFAULT_CAPACITY), "TEST FAILURE: Bag did not maintain capacity on overflow"

def main():
    """
        Concept Tests
    """
    test_concept_termlinking()


    """
        Table Tests
    """
    NARS.NARS()
    test_table_removemax()
    test_table_removemin()

    """
     Buffer Tests
    """
    test_buffer_removemax()
    test_buffer_removemin()

    """
        Bag Tests
    """
    test_bag_overflow_purge()

    print("All Data Structure Tests successfully passed.")

if __name__ == "__main__":
    main()