def schedule_maximum_matches(matches):
    """Greedy interval scheduling: select a maximum non-overlapping set."""
    intervals = []
    for match in matches:
        if "start" not in match or "end" not in match:
            raise ValueError("Every match needs a start and end time.")
        start, end = match["start"], match["end"]
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise ValueError("Match times must be numeric.")
        if start > end:
            raise ValueError("A match cannot end before it starts.")
        intervals.append(match)

    selected, end_time = [], float("-inf")
    for match in sorted(intervals, key=lambda item: (item["end"], item["start"])):
        if match["start"] >= end_time:
            selected.append(match)
            end_time = match["end"]
    return selected
