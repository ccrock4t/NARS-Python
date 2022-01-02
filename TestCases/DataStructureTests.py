import random

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
    table = NARSDataStructures.Other.Table(item_type=NALGrammar.Sentences.Judgment)
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    maximum = max(confidences)
    for c in confidences:
        sentence = NALGrammar.Sentences.Judgment(
            NALGrammar.Terms.StatementTerm(NALGrammar.Terms.from_string("a"),
                                           NALGrammar.Terms.from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.Values.TruthValue(0.9, c))
        table.put(sentence)
    tablemax = table.extract_max().value.confidence
    assert (tablemax == maximum), "TEST FAILURE: Table did not properly retrieve maximum value"


def test_table_removemin():
    """
        Test if the Table can successfully remove its minimum value
    """
    table = NARSDataStructures.Other.Table(item_type=NALGrammar.Sentences.Judgment)
    confidences = [0.6, 0.2, 0.99, 0.5, 0.9]
    minimum = min(confidences)
    for c in confidences:
        # make sentence <a --> b>. %0.9;c%
        sentence = NALGrammar.Sentences.Judgment(
            NALGrammar.Terms.StatementTerm(NALGrammar.Terms.from_string("a"),
                                           NALGrammar.Terms.from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.Values.TruthValue(0.9, c))
        table.put(sentence)

    tablemin = table.extract_min().value.confidence
    assert (tablemin == minimum), "TEST FAILURE: Table did not properly retrieve minimum value"


def test_table_overflow_purge():
    """
        Test if table stays within capacity when it overflows.
    """
    test_data_structure = NARSDataStructures.Other.\
        Table(item_type=NALGrammar.Sentences.Judgment)
    items_added = 0
    max_capacity = NARS.Config.TABLE_DEFAULT_CAPACITY
    for i in range(0, max_capacity + 5):
        test_data_structure.put(NALGrammar.Sentences.new_sentence_from_string("(a-->b)."))
        items_added += 1
        if items_added <= max_capacity:
            assert len(
                test_data_structure) == items_added, "TEST FAILURE: Length of bag does not equal # of items added"

    assert (items_added > max_capacity), "TEST FAILURE: For this test, add more items than the capacity"
    assert (len(test_data_structure) == max_capacity), "TEST FAILURE: " + type(
        test_data_structure).__name__ + " did not maintain capacity on overflow"


def test_buffer_removemax():
    """
        Test if the Buffer can successfully remove its maximum value
    """
    buffer = NARSDataStructures.Buffers.Buffer(NARSDataStructures.Other.Task, capacity=10)
    priorities = [0.6, 0.2, 0.99, 0.5, 0.9]
    maximum = max(priorities)
    for p in priorities:
        sentence = NALGrammar.Sentences.Judgment(
            NALGrammar.Terms.StatementTerm(NALGrammar.Terms.from_string("a"),
                                           NALGrammar.Terms.from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.Values.TruthValue(0.9, 0.9))
        item = NARSDataStructures.ItemContainers.Item(NARSDataStructures.Other.Task(sentence), -1)
        item.budget.set_priority(p)
        buffer.put(item)
    buffermax = buffer.extract_max().budget.get_priority()
    assert (buffermax == maximum), "TEST FAILURE: Buffer did not properly retrieve maximum value"


def test_buffer_removemin():
    """
        Test if the Table can successfully remove its minimum value
    """
    buffer = NARSDataStructures.Buffers.Buffer(NARSDataStructures.Other.Task, capacity=10)
    priorities = [0.6, 0.2, 0.99, 0.5, 0.9]
    minimum = min(priorities)
    for p in priorities:
        # make sentence <a --> b>. %0.9;c%
        sentence = NALGrammar.Sentences.Judgment(
            NALGrammar.Terms.StatementTerm(NALGrammar.Terms.from_string("a"),
                                           NALGrammar.Terms.from_string("b"), NALSyntax.Copula.Inheritance),
            NALGrammar.Values.TruthValue(0.9, 0.9))
        item = NARSDataStructures.ItemContainers.Item(NARSDataStructures.Other.Task(sentence), -1)
        item.budget.set_priority(p)
        buffer.put(item)

    buffermin = buffer.extract_min().budget.get_priority()
    assert (buffermin == minimum), "TEST FAILURE: Buffer did not properly retrieve minimum value"


def test_concept_termlinking():
    """
        Test if term links can be added and removed properly from a concept
    """
    memory = NARSMemory.Memory()
    statement_concept = memory.peek_concept(NALGrammar.Terms.from_string("(A-->B)"))
    conceptA = memory.peek_concept(NALGrammar.Terms.from_string("A"))
    conceptB = memory.peek_concept(NALGrammar.Terms.from_string("B"))

    assert (len(statement_concept.term_links) == 2), "TEST FAILURE: Concept " + str(
        statement_concept) + " does not have 2 termlinks"
    assert (len(conceptA.term_links) == 1), "TEST FAILURE: Concept " + str(
        conceptA) + " does not have 1 termlink. Has: " + str(conceptA.term_links.count)
    assert (len(conceptB.term_links) == 1), "TEST FAILURE: Concept " + str(
        conceptB) + " does not have 1 termlink. Has: " + str(conceptB.term_links.count)

    statement_concept.remove_term_link(conceptA)  # remove concept A's termlink

    assert (len(statement_concept.term_links) == 1), "Concept " + str(statement_concept) + " does not have 1 termlink"
    assert (len(conceptA.term_links) == 0), "TEST FAILURE: Concept " + str(conceptA) + " does not have 0 termlinks"
    assert (len(conceptB.term_links) == 1), "TEST FAILURE: Concept " + str(conceptB) + " does not have 1 termlink"

    take = statement_concept.term_links.take_using_key(NARSDataStructures.ItemContainers.Item.get_key_from_object(
        conceptB)).object  # take out the only remaining concept (concept B)

    assert (take == conceptB), "TEST FAILURE: Removed concept was not Concept 'B'"
    assert (len(conceptB.term_links) == 1), "TEST FAILURE: Concept does not have 1 termlink"


def test_bag_overflow_purge():
    """
        Test if bag stays within capacity when it overflows.
    """
    max_capacity = 10
    test_data_structure = NARSDataStructures.Bag.Bag(item_type=NALGrammar.Sentences.Sentence, capacity=max_capacity)
    items_added = 0

    for i in range(0, max_capacity + 5):
        test_data_structure.put_new(NALGrammar.Sentences.new_sentence_from_string("(a-->b)."))
        items_added += 1
        if items_added <= max_capacity:
            assert len(
                test_data_structure) == items_added, "TEST FAILURE: Length of bag does not equal # of items added"

    assert (items_added > max_capacity), "TEST FAILURE: For this test, add more items than the capacity"
    assert (len(test_data_structure) == max_capacity), "TEST FAILURE: " + type(
        test_data_structure).__name__ + " did not maintain capacity on overflow"


def test_bag_clear():
    """
        Test if bag stays within capacity when it overflows.
    """
    max_capacity = 5
    test_data_structure = NARSDataStructures.Bag.Bag(item_type=NALGrammar.Sentences.Sentence, capacity=max_capacity)
    items_added = 0

    for i in range(0, max_capacity):
        test_data_structure.put_new(NALGrammar.Sentences.new_sentence_from_string("(a-->b)."))
        items_added += 1
        if items_added <= max_capacity:
            assert len(
                test_data_structure) == items_added, "TEST FAILURE: Length of bag does not equal # of items added"

    test_data_structure.clear()

    assert len(test_data_structure) == 0, "TEST FAILURE: This test should empty the bag completelyy"


def test_bag_priority_changing():
    """
        Test if bag stays within capacity when it overflows.
    """
    max_capacity = 10
    test_data_structure = NARSDataStructures.Bag.Bag(item_type=NALGrammar.Sentences.Sentence, capacity=max_capacity)
    items_added = 0

    expected_values = {}
    for i in range(0, max_capacity):
        item = test_data_structure.put_new(NALGrammar.Sentences.new_sentence_from_string("(a-->b)."))
        new_priority = random.random()
        test_data_structure.change_priority(item.key, new_priority)
        expected_values[item.key] = item.get_bag_number()
        items_added += 1

    counts = {}
    for key in test_data_structure.item_keys:
        if key not in counts:
            counts[key] = 1
        else:
            counts[key] += 1

    for key in expected_values.keys():
        assert (counts[key] == expected_values[
            key]), "TEST FAILURE: Priority change did not remove/add proper number of values in Bag " + str(
            (counts[key], expected_values[key]))


def test_bag_priority_changing():
    """
        Test if changing priority works in bag
    """
    max_capacity = 10
    bag = NARSDataStructures.Bag.Bag(item_type=NALGrammar.Sentences.Sentence, capacity=max_capacity)
    items_added = 0

    expected_values = {}
    for i in range(0, max_capacity):
        item = bag.put_new(NALGrammar.Sentences.new_sentence_from_string("(a-->b)."))
        new_priority = random.random()
        bag.change_priority(item.key, new_priority)
        expected_values[item.key] = new_priority
        items_added += 1

    for i in range(len(bag)):
        key = bag.item_keys[i]
        item = bag.item_lookup_dict[key]
        priority = item.budget.get_priority()
        assert (priority == expected_values[key]), "TEST FAILURE: Priority value was not changed as expected " + str(
            (priority, expected_values[key]))


def test_4_event_temporal_chaining():
    calculate_expected_num_of_results = lambda N: int(N * (N + 1) / 2 - 1)

    capacities = [2, 3, 6, 10]

    for capacity in capacities:
        event_buffer = NARSDataStructures.Buffers.TemporalModule(NARS=None, item_type=NARSDataStructures.Other.Task,
                                                                 capacity=capacity)

        for i in range(capacity):
            event_buffer.put_new(NARSDataStructures.Other.Task(
                NALGrammar.Sentences.new_sentence_from_string("(a" + str(i) + "-->b" + str(i) + "). :|:")))

        actual = len(event_buffer.temporal_chaining_4())
        expected = calculate_expected_num_of_results(capacity)
        assert actual == expected, "ERROR: Event buffer of size " + str(capacity) + " produced " + str(
            actual) + " results, instead of expected " + str(expected)


def main():
    """
        Concept Tests
    """
    test_concept_termlinking()

    """
        Table Tests
    """
    Global.Global.NARS = NARS.NARS()  # need it for Stamp IDs
    test_table_removemax()
    test_table_removemin()
    test_table_overflow_purge()

    """
     Buffer Tests
    """
    test_buffer_removemax()
    test_buffer_removemin()
    # test_event_buffer_processing()

    """
        Bag Tests
    """
    test_bag_overflow_purge()
    test_bag_clear()
    test_bag_priority_changing()

    print("All Data Structure Tests successfully passed.")


if __name__ == "__main__":
    main()
