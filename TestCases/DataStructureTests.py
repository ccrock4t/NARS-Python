import Global
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
    table = NARSDataStructures.Table(item_type=NALGrammar.Judgment)
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    maximum = max(confidences)
    for c in confidences:
        sentence = NALGrammar.Judgment(
            NALGrammar.Statement(NALGrammar.Term.from_string("a"), NALGrammar.Term.from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.TruthValue(0.9, c))
        table.put(sentence)
    tablemax = table._extract_max().value.confidence
    assert(tablemax == maximum), "TEST FAILURE: Table did not properly retrieve maximum value"


def test_table_removemin():
    """
        Test if the Table can successfully remove its minimum value
    """
    table = NARSDataStructures.Table(item_type=NALGrammar.Judgment)
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    minimum = min(confidences)
    for c in confidences:
        #make sentence <a --> b>. %0.9;c%
        sentence = NALGrammar.Judgment(
            NALGrammar.Statement(NALGrammar.Term.from_string("a"), NALGrammar.Term.from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.TruthValue(0.9, c))
        table.put(sentence)

    tablemin = table._extract_min().value.confidence
    assert (tablemin == minimum), "TEST FAILURE: Table did not properly retrieve minimum value"

def test_table_overflow_purge():
    """
        Test if table stays within capacity when it overflows.
    """
    test_data_structure = NARSDataStructures.Table(item_type=NALGrammar.Judgment)
    items_added = 0
    max_capacity = NARS.Config.TABLE_DEFAULT_CAPACITY
    for i in range(0, max_capacity + 5):
        test_data_structure.put(NALGrammar.Sentence.new_sentence_from_string("(a-->b)."))
        items_added += 1
        if items_added <= max_capacity:
            assert len(test_data_structure) == items_added,"TEST FAILURE: Length of bag does not equal # of items added"

    assert (items_added > max_capacity), "TEST FAILURE: For this test, add more items than the capacity"
    assert (len(test_data_structure) == max_capacity), "TEST FAILURE: " + type(test_data_structure).__name__ + " did not maintain capacity on overflow"

def test_buffer_removemax():
    """
        Test if the Table can successfully remove its maximum value
    """
    buffer = NARSDataStructures.Buffer(NALGrammar.Sentence)
    priorities = [0.6, 0.2, 0.99, 0.5, 0.9]
    maximum = max(priorities)
    for p in priorities:
        sentence = NALGrammar.Judgment(
            NALGrammar.Statement(NALGrammar.Term.from_string("a"), NALGrammar.Term.from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.TruthValue(0.9, 0.9))
        item = NARSDataStructures.ItemContainer.Item(sentence,-1)
        item.budget.priority = p
        buffer.put(item)
    buffermax = buffer._extract_max().budget.priority
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
            NALGrammar.Statement(NALGrammar.Term.from_string("a"), NALGrammar.Term.from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.TruthValue(0.9, 0.9))
        item = NARSDataStructures.ItemContainer.Item(sentence,-1)
        item.budget.priority = p
        buffer.put(item)

    buffermin = buffer._extract_min().budget.priority
    assert (buffermin == minimum), "TEST FAILURE: Buffer did not properly retrieve minimum value"



def test_concept_termlinking():
    """
        Test if term links can be added and removed properly from a concept
    """
    memory = NARSMemory.Memory()
    statement_concept = memory.peek_concept(NALGrammar.Term.from_string("(A-->B)"))
    conceptA = memory.peek_concept(NALGrammar.Term.from_string("A"))
    conceptB = memory.peek_concept(NALGrammar.Term.from_string("B"))

    assert (statement_concept.term_links.count == 2), "TEST FAILURE: Concept " + str(statement_concept) + " does not have 2 termlinks"
    assert (conceptA.term_links.count == 1), "TEST FAILURE: Concept " + str(conceptA) + " does not have 1 termlink. Has: " + str(conceptA.term_links.count)
    assert (conceptB.term_links.count == 1), "TEST FAILURE: Concept " + str(conceptB) + " does not have 1 termlink. Has: " + str(conceptB.term_links.count)

    statement_concept.remove_term_link(conceptA) # remove concept A's termlink

    assert (statement_concept.term_links.count == 1), "Concept " + str(statement_concept) + " does not have 1 termlink"
    assert (conceptA.term_links.count == 0), "TEST FAILURE: Concept " + str(conceptA) + " does not have 0 termlinks"
    assert (conceptB.term_links.count == 1), "TEST FAILURE: Concept " + str(conceptB) + " does not have 1 termlink"

    take = statement_concept.term_links.take_using_key(NARSDataStructures.ItemContainer.Item.get_key_from_object(conceptB)).object # take out the only remaining concept (concept B)

    assert (take == conceptB), "TEST FAILURE: Removed concept was not Concept 'B'"
    assert (conceptB.term_links.count == 1), "TEST FAILURE: Concept does not have 1 termlink"


def test_bag_overflow_purge():
    """
        Test if bag stays within capacity when it overflows.
    """
    test_data_structure = NARSDataStructures.Bag(item_type=NALGrammar.Sentence)
    items_added = 0
    max_capacity = NARS.Config.BAG_DEFAULT_CAPACITY
    for i in range(0, max_capacity + 5):
        test_data_structure.put_new(NALGrammar.Sentence.new_sentence_from_string("(a-->b)."))
        items_added += 1
        if items_added <= max_capacity:
            assert len(test_data_structure) == items_added,"TEST FAILURE: Length of bag does not equal # of items added"

    assert (items_added > max_capacity), "TEST FAILURE: For this test, add more items than the capacity"
    assert (test_data_structure.count == max_capacity), "TEST FAILURE: " +  + type(test_data_structure).__name__ +  + " did not maintain capacity on overflow"

def main():
    """
        Concept Tests
    """
    test_concept_termlinking()


    """
        Table Tests
    """
    Global.Global.NARS = NARS.NARS() # need it for Stamp IDs
    test_table_removemax()
    test_table_removemin()
    test_table_overflow_purge()

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