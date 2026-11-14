def selection_sort(arr):
    """
    Selection Sort algorithm.
    Time Complexity: O(n^2) for all cases.
    Space Complexity: O(1)
    """
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr

if __name__ == "__main__":
    test_arr = [64, 25, 12, 22, 11]
    print("Original array:", test_arr)
    sorted_arr = selection_sort(test_arr.copy())
    print("Sorted array:", sorted_arr)
