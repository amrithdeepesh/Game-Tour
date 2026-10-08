def schedule_maximum_matches(matches):
    """Greedy interval scheduling: choose the most non-overlapping matches."""
    selected, end_time = [], float("-inf")
    for match in sorted(matches, key=lambda item: (item["end"], item["start"])):
        if match["start"] >= end_time:
            selected.append(match)
            end_time = match["end"]
    return selected
