def merge_sort(arr):
    """
    Merge Sort algorithm using divide and conquer.
    Time Complexity: O(n log n) for all cases.
    Space Complexity: O(n)
    """
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left_half = merge_sort(arr[:mid])
    right_half = merge_sort(arr[mid:])

    return _merge(left_half, right_half)

def _merge(left, right):
    sorted_array = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            sorted_array.append(left[i])
            i += 1
        else:
            sorted_array.append(right[j])
            j += 1

    sorted_array.extend(left[i:])
    sorted_array.extend(right[j:])
    return sorted_array

if __name__ == "__main__":
    test_arr = [12, 11, 13, 5, 6, 7]
    print("Original array:", test_arr)
    sorted_arr = merge_sort(test_arr)
    print("Sorted array:", sorted_arr)
