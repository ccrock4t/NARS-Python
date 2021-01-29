import NARSDataStructures

def maxheaptest_insert3_removemax():
    heap = NARSDataStructures.MaxHeap()
    insert = [1, 3, 6]
    maximum = max(insert)
    for i in insert:
        heap.insert(i)

    heapmax = heap.extractMax()
    assert(heapmax == maximum), "Heap did not properly retrieve maximum value"

def maxheaptest_insert3_removemin():
    heap = NARSDataStructures.MaxHeap()
    insert = [1, 3, 6]
    minimum = min(insert)
    for i in insert:
        heap.insert(i)

    heapmin = heap.extractMin()
    assert (heapmin == minimum), "Heap did not properly retrieve minimum value"

if __name__ == "__main__":
    """
        MaxHeap Tests
    """
    maxheaptest_insert3_removemax()
    print("Everything passed")