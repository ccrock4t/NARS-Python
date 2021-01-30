import NARSDataStructures

def test_maxheap_removemax():
    heap = NARSDataStructures.MaxHeap()
    insert = [1, 2, 3, 4, 5, 6]
    maximum = max(insert)
    for i in insert:
        heap.insert(i)

    heapmax = heap.extractMax()
    assert(heapmax == maximum), "Heap did not properly retrieve maximum value"


def test_maxheap_removemin():
    heap = NARSDataStructures.MaxHeap()
    insert = [1, 2, 3, 4, 5, 6]
    minimum = min(insert)
    for i in insert:
        heap.insert(i)

    heapmin = heap.extractMin()
    assert (heapmin == minimum), "Heap did not properly retrieve minimum value"


if __name__ == "__main__":
    """
        MaxHeap Tests
    """
    test_maxheap_removemax()
    test_maxheap_removemin()
    print("Everything passed")