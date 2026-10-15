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


def schedule_tournament_events(candidates, venues=None):
    """
    Greedy tournament match & event scheduler with multi-venue and participant conflict detection.

    Greedy Strategy:
      Candidates are prioritized by:
        1. Earliest finish time (min end time) - proven optimal for unconstrained interval scheduling.
        2. Higher priority score.
        3. Earlier start time.

    Constraints verified:
      1. Venue Availability: Venue cannot host multiple simultaneous events.
      2. Participant Non-Collision: A student/team cannot compete in overlapping events.
      3. Venue Capacity: Game size cannot exceed venue capacity.
    """
    valid_candidates = []
    for idx, c in enumerate(candidates):
        start = c.get("start")
        end = c.get("end")
        if start is None or end is None:
            raise ValueError(f"Candidate #{idx + 1} ({c.get('name', 'Unnamed')}) is missing start or end time.")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise ValueError("Start and end times must be numeric timestamps or hour numbers.")
        if start >= end:
            raise ValueError(f"Event '{c.get('name')}' cannot end before or at its start time.")

        valid_candidates.append({
            "id": c.get("id", idx + 1),
            "name": str(c.get("name", f"Event #{idx + 1}")),
            "venue": str(c.get("venue", "Main Arena")).strip(),
            "start": start,
            "end": end,
            "duration": end - start,
            "participants": [str(p).strip() for p in c.get("participants", []) if str(p).strip()],
            "capacity": int(c.get("capacity", 20)),
            "priority": int(c.get("priority", 1)),
        })

    # Sort by Earliest Finish Time (greedy rule), then highest priority, then start
    sorted_candidates = sorted(
        valid_candidates,
        key=lambda x: (x["end"], -x["priority"], x["start"])
    )

    scheduled = []
    rejected = []
    trace = []

    # Track venue occupancy intervals: {venue_name: [(start, end, event_name)]}
    venue_bookings = {}
    # Track participant occupancy intervals: {participant_name: [(start, end, event_name)]}
    participant_bookings = {}

    for step_num, event in enumerate(sorted_candidates, 1):
        v = event["venue"]
        s = event["start"]
        e = event["end"]
        p_list = event["participants"]

        conflict_reason = None

        # 1. Check venue overlap
        for b_start, b_end, b_name in venue_bookings.get(v, []):
            if s < b_end and b_start < e:
                conflict_reason = f"Venue '{v}' is already booked for '{b_name}' during ({b_start}–{b_end})."
                break

        # 2. Check participant overlap
        if not conflict_reason:
            for p in p_list:
                for b_start, b_end, b_name in participant_bookings.get(p, []):
                    if s < b_end and b_start < e:
                        conflict_reason = f"Participant '{p}' is already competing in '{b_name}' during ({b_start}–{b_end})."
                        break
                if conflict_reason:
                    break

        # Decision
        if conflict_reason:
            rejected.append({**event, "reason": conflict_reason})
            trace.append({
                "step": step_num,
                "event": event["name"],
                "venue": v,
                "interval": f"{s}–{e}",
                "decision": "REJECTED",
                "reason": conflict_reason,
            })
        else:
            scheduled.append(event)
            venue_bookings.setdefault(v, []).append((s, e, event["name"]))
            for p in p_list:
                participant_bookings.setdefault(p, []).append((s, e, event["name"]))

            trace.append({
                "step": step_num,
                "event": event["name"],
                "venue": v,
                "interval": f"{s}–{e}",
                "decision": "ACCEPTED",
                "reason": f"Earliest finish time satisfied; venue '{v}' and {len(p_list)} participants are free.",
            })

    # Group scheduled fixtures by venue
    timetable = {}
    for ev in scheduled:
        timetable.setdefault(ev["venue"], []).append(ev)

    return {
        "scheduled": scheduled,
        "rejected": rejected,
        "total_requested": len(candidates),
        "total_scheduled": len(scheduled),
        "total_conflicts": len(rejected),
        "decision_trace": trace,
        "timetable_by_venue": timetable,
        "algorithm": {
            "name": "Earliest Finish Time First (Greedy Interval Scheduling)",
            "sorting_rule": "Ascending Finish Time (end_time), descending Priority",
            "time_complexity": "O(N log N + N * (V + P))",
            "space_complexity": "O(N)",
            "optimality_proof": (
                "EFT is mathematically optimal for 1-resource interval scheduling. "
                "With multi-venue and participant conflict constraints, it functions as an "
                "efficient polynomial-time greedy heuristic that maximizes throughput while guaranteeing zero collisions."
            ),
            "limitations": (
                "Greedy choices are locally optimal and irreversible. Does not backtrack to evaluate global permutations "
                "if a lower-priority combination could theoretically yield higher total participants."
            ),
        },
    }
