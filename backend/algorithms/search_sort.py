import time
import random


def linear_search(items, key, field="name"):
    """Return the first exact case-insensitive match, or -1."""
    target = str(key).casefold()
    for index, item in enumerate(items):
        if str(item.get(field, "")).casefold() == target:
            return index
    return -1


def linear_search_detailed(items, key, field="name"):
    """Linear search with step-by-step comparison trace for Data Structures Lab."""
    target = str(key).casefold()
    steps = []
    comparisons = 0
    found_idx = -1

    for index, item in enumerate(items):
        comparisons += 1
        val = str(item.get(field, ""))
        matched = val.casefold() == target
        steps.append({
            "step": comparisons,
            "index": index,
            "value": val,
            "target": str(key),
            "matched": matched,
            "action": f"Checked index {index} ('{val}'). {'MATCH FOUND!' if matched else 'No match, advancing to next.'}"
        })
        if matched:
            found_idx = index
            break

    return {
        "found": found_idx != -1,
        "index": found_idx,
        "item": items[found_idx] if found_idx != -1 else None,
        "comparisons": comparisons,
        "total_items": len(items),
        "steps": steps,
        "time_complexity": "O(n)",
        "space_complexity": "O(1)"
    }


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


def binary_search_detailed(items, key, field="name"):
    """Binary search with left, middle, right indices and step comparisons."""
    # Check if items are sorted by field
    is_sorted = True
    for i in range(len(items) - 1):
        if str(items[i].get(field, "")).casefold() > str(items[i + 1].get(field, "")).casefold():
            is_sorted = False
            break

    search_pool = items if is_sorted else sorted(items, key=lambda x: str(x.get(field, "")).casefold())
    target = str(key).casefold()

    low, high = 0, len(search_pool) - 1
    steps = []
    comparisons = 0
    found_idx = -1

    while low <= high:
        comparisons += 1
        middle = (low + high) // 2
        curr_item = search_pool[middle]
        val = str(curr_item.get(field, ""))
        val_fold = val.casefold()

        if val_fold == target:
            steps.append({
                "step": comparisons,
                "low": low,
                "middle": middle,
                "high": high,
                "middle_value": val,
                "target": str(key),
                "action": f"Middle index {middle} ('{val}') matches target! Search successful."
            })
            found_idx = middle
            break
        elif val_fold < target:
            steps.append({
                "step": comparisons,
                "low": low,
                "middle": middle,
                "high": high,
                "middle_value": val,
                "target": str(key),
                "action": f"'{val}' < '{key}'. Target lies in right subarray: set low = {middle + 1}."
            })
            low = middle + 1
        else:
            steps.append({
                "step": comparisons,
                "low": low,
                "middle": middle,
                "high": high,
                "middle_value": val,
                "target": str(key),
                "action": f"'{val}' > '{key}'. Target lies in left subarray: set high = {middle - 1}."
            })
            high = middle - 1

    return {
        "found": found_idx != -1,
        "index": found_idx,
        "item": search_pool[found_idx] if found_idx != -1 else None,
        "comparisons": comparisons,
        "was_sorted": is_sorted,
        "pool": search_pool,
        "steps": steps,
        "time_complexity": "O(log n)",
        "space_complexity": "O(1)"
    }


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


def merge_sort_detailed(items, field="points", descending=True):
    """
    Merge sort from scratch with full splitting and merging step trace for Data Structures Lab.
    """
    splits = []
    merges = []
    comparison_counter = [0]

    def _format_item(x):
        return f"{x.get('name', 'Item')}: {x.get(field, 0)}"

    def _sort(sublist, depth=0, label="root"):
        n = len(sublist)
        if n <= 1:
            return [dict(x) for x in sublist]

        mid = n // 2
        left_raw = sublist[:mid]
        right_raw = sublist[mid:]

        splits.append({
            "depth": depth,
            "label": label,
            "original": [_format_item(x) for x in sublist],
            "left": [_format_item(x) for x in left_raw],
            "right": [_format_item(x) for x in right_raw]
        })

        left = _sort(left_raw, depth + 1, f"{label}.L")
        right = _sort(right_raw, depth + 1, f"{label}.R")

        merged = []
        i = j = 0
        step_comparisons = []

        while i < len(left) and j < len(right):
            comparison_counter[0] += 1
            val_a = left[i].get(field, 0)
            val_b = right[j].get(field, 0)
            take_left = val_a >= val_b if descending else val_a <= val_b
            step_comparisons.append({
                "left_item": _format_item(left[i]),
                "right_item": _format_item(right[j]),
                "chosen": _format_item(left[i]) if take_left else _format_item(right[j])
            })
            if take_left:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1

        merged.extend(left[i:])
        merged.extend(right[j:])

        merges.append({
            "depth": depth,
            "label": label,
            "left": [_format_item(x) for x in left],
            "right": [_format_item(x) for x in right],
            "comparisons": step_comparisons,
            "merged": [_format_item(x) for x in merged]
        })

        return merged

    sorted_result = _sort(items)

    return {
        "original": items,
        "sorted": sorted_result,
        "splits": splits,
        "merges": merges,
        "total_comparisons": comparison_counter[0],
        "field": field,
        "descending": descending,
        "time_complexity": "O(n log n)",
        "space_complexity": "O(n)"
    }


def benchmark_search_sort():
    """
    Measures actual runtime in microseconds across varying sizes (10, 50, 100, 500, 1000)
    for Linear Search, Binary Search, Merge Sort, and Selection Sort.
    """
    sizes = [10, 50, 100, 250, 500]
    results = []

    for n in sizes:
        sample = [{"name": f"Student_{i}", "points": random.randint(1, 1000)} for i in range(n)]
        target_name = f"Student_{n // 2}"
        sorted_sample = sorted(sample, key=lambda x: x["name"])

        # Linear Search
        t0 = time.perf_counter()
        linear_search(sample, target_name)
        t_linear = (time.perf_counter() - t0) * 1_000_000  # microseconds

        # Binary Search
        t0 = time.perf_counter()
        binary_search(sorted_sample, target_name)
        t_binary = (time.perf_counter() - t0) * 1_000_000

        # Merge Sort
        t0 = time.perf_counter()
        merge_sort(sample, "points")
        t_merge = (time.perf_counter() - t0) * 1_000_000

        # Selection Sort
        t0 = time.perf_counter()
        selection_sort(sample, "points")
        t_selection = (time.perf_counter() - t0) * 1_000_000

        results.append({
            "n": n,
            "linear_search_us": round(t_linear, 2),
            "binary_search_us": round(t_binary, 2),
            "merge_sort_us": round(t_merge, 2),
            "selection_sort_us": round(t_selection, 2),
        })

    return {
        "benchmarks": results,
        "complexities": {
            "linear_search": {"best": "O(1)", "average": "O(n)", "worst": "O(n)", "space": "O(1)"},
            "binary_search": {"best": "O(1)", "average": "O(log n)", "worst": "O(log n)", "space": "O(1)"},
            "merge_sort": {"best": "O(n log n)", "average": "O(n log n)", "worst": "O(n log n)", "space": "O(n)"},
            "selection_sort": {"best": "O(n²)", "average": "O(n²)", "worst": "O(n²)", "space": "O(1)"},
        }
    }
