def linear_search(items, key, field="name"):
    target = str(key).casefold()
    for index, item in enumerate(items):
        if str(item.get(field, "")).casefold() == target:
            return index
    return -1

def binary_search(items, key, field="name"):
    """Binary search a list already sorted by field; returns matching index or -1."""
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
    result = [dict(item) for item in items]
    for start in range(len(result)):
        best = start
        for index in range(start + 1, len(result)):
            a, b = result[index].get(field), result[best].get(field)
            if (a > b) if descending else (a < b):
                best = index
        result[start], result[best] = result[best], result[start]
    return result

def merge_sort(items, field="points", descending=True):
    if len(items) <= 1:
        return [dict(item) for item in items]
    middle = len(items) // 2
    left = merge_sort(items[:middle], field, descending)
    right = merge_sort(items[middle:], field, descending)
    result = []
    while left and right:
        a, b = left[0].get(field), right[0].get(field)
        take_left = a >= b if descending else a <= b
        result.append(left.pop(0) if take_left else right.pop(0))
    return result + left + right
