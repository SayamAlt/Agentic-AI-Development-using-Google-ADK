def quick_sort(arr):
    """
    Quick Sort algorithm using divide and conquer.
    Time Complexity: O(n log n) average case, O(n^2) worst case.
    Space Complexity: O(log n) for recursion stack.
    """
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)

if __name__ == "__main__":
    test_arr = [38, 27, 43, 3, 9, 82, 10]
    print("Original array:", test_arr)
    sorted_arr = quick_sort(test_arr)
    print("Sorted array:", sorted_arr)
