def insertion_sort(arr):
    """
    Insertion Sort algorithm.
    Time Complexity: O(n^2) average and worst case, O(n) best case.
    Space Complexity: O(1)
    """
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

if __name__ == "__main__":
    test_arr = [12, 11, 13, 5, 6]
    print("Original array:", test_arr)
    sorted_arr = insertion_sort(test_arr.copy())
    print("Sorted array:", sorted_arr)
