def linear_search(items, key, field="name"):
    """Return the first exact case-insensitive match, or -1."""
    target = str(key).casefold()
    for index, item in enumerate(items):
        if str(item.get(field, "")).casefold() == target:
            return index
    return -1


def binary_search(items, key, field="name"):
    """Search items sorted ascending by field; returns the matching index or -1."""
    target = str(key).casefold()
    low, high = 0, len(items) - 1
    while low <= high:
        middle = (low + high) // 2
        value = str(items[middle].get(field, "")).casefold()
        if value == target:
            return middle
        if value < target:
            low = middle + 1
        else:
            high = middle - 1
    return -1


def selection_sort(items, field="points", descending=True):
    """Selection sort; O(n²) time and O(n) copy space."""
    result = [dict(item) for item in items]
    for start in range(len(result)):
        best = start
        for index in range(start + 1, len(result)):
            current, selected = result[index].get(field), result[best].get(field)
            if (current > selected) if descending else (current < selected):
                best = index
        result[start], result[best] = result[best], result[start]
    return result


def merge_sort(items, field="points", descending=True):
    """Stable merge sort; O(n log n) time and O(n) additional space."""
    if len(items) <= 1:
        return [dict(item) for item in items]

    middle = len(items) // 2
    left = merge_sort(items[:middle], field, descending)
    right = merge_sort(items[middle:], field, descending)
    merged = []
    left_index = right_index = 0

    while left_index < len(left) and right_index < len(right):
        first = left[left_index].get(field)
        second = right[right_index].get(field)
        take_left = first >= second if descending else first <= second
        if take_left:
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1

    merged.extend(left[left_index:])
    merged.extend(right[right_index:])
    return merged
