"""
Live Database Seeder for Game Tour DSA Platform
Seeds fresh real data:
- Factions (Falcons, Tigers, Sharks, Eagles)
- Administrator (admin1)
- Real students with 8-character passwords across all factions
- 7 Tournament games strictly at the 7 allowed venues
- Real choices, matches, and recorded results
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath("backend"))
import database
from app import password_hash

def seed():
    print("Clearing MySQL tables...")
    conn = database.connect()
    cur = conn.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tables = [
        "result_audit", "results", "matches", "waiting_lists",
        "game_choices", "games", "tournaments", "sessions",
        "announcements", "factions", "users"
    ]
    for t in tables:
        cur.execute(f"TRUNCATE TABLE {t};")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()
    conn.close()

    print("Re-initializing database schema & default admin...")
    database._ready = False
    database.init()

    # 1. Admin setup (ensure admin1 exists with default password)
    admin_hash = password_hash("Din@pr@bh@7012760095")
    database.query(
        "UPDATE users SET password_hash = %s WHERE username = 'admin1'",
        (admin_hash,)
    )
    print("Admin 'admin1' configured.")

    # 2. Factions managed by admin
    admin_user = database.user_by_username("admin1")
    cur_factions = [f["name"] for f in database.factions()]
    for f in ["Falcons", "Tigers", "Sharks", "Eagles"]:
        if f not in cur_factions:
            database.create_faction(f, f"{f} Championship Division", admin_user["id"])
    print(f"Factions ready: {[f['name'] for f in database.factions()]}")

    # 3. Real Students (with exactly 8-char passwords)
    students_data = [
        {"username": "aarav_s", "name": "Aarav Sharma", "email": "aarav@student.edu", "faction": "Falcons", "pass": "pass1234"},
        {"username": "priya_n", "name": "Priya Nair", "email": "priya@student.edu", "faction": "Tigers", "pass": "pass5678"},
        {"username": "rohan_i", "name": "Rohan Iyer", "email": "rohan@student.edu", "faction": "Sharks", "pass": "pass9012"},
        {"username": "ananya_r", "name": "Ananya Rao", "email": "ananya@student.edu", "faction": "Eagles", "pass": "pass3456"},
    ]

    student_ids = []
    for s in students_data:
        h = password_hash(s["pass"])
        uid = database.create_user(
            {"username": s["username"], "name": s["name"], "email": s["email"], "faction": s["faction"]},
            h
        )
        student_ids.append(uid)
        print(f"Created student {s['name']} (@{s['username']}) - Faction: {s['faction']}")

    # 4. Tournament creation
    tid = database.create_tournament({
        "name": "Inter-Faction Campus Championship 2026",
        "description": "Grand multi-sport tournament across all 7 collegiate venues.",
        "registration_closes_at": (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"),
        "points_first": 10,
        "points_second": 7,
        "points_third": 5,
        "points_participation": 1,
    })
    print(f"Tournament created: ID {tid}")

    # 5. 7 Games strictly on the 7 allowed venues (non-overlapping start times)
    venues_schedule = [
        ("Cricket Championship Match", "Cricket Ground", "2026-11-05 09:00:00", 22, 1, 90),
        ("Basketball 3x3 Tournament", "Basketball Court", "2026-11-05 10:45:00", 12, 2, 60),
        ("Volleyball Inter-Faction Cup", "Volleyball Court", "2026-11-05 12:00:00", 16, 2, 60),
        ("Badminton Open Singles", "Badminton Court", "2026-11-05 13:30:00", 16, 3, 45),
        ("Table Tennis Grand Arena", "Indoor Sports Complex", "2026-11-05 14:30:00", 20, 3, 60),
        ("Tennis Singles Quarterfinals", "Tennis Court", "2026-11-05 16:00:00", 8, 2, 75),
        ("Track & Field 100m Sprint", "Athletics Track", "2026-11-05 17:30:00", 30, 1, 45),
    ]

    game_ids = []
    for name, venue, starts, cap, rounds, dur in venues_schedule:
        gid = database.create_game({
            "tournament_id": tid,
            "name": name,
            "venue": venue,
            "starts_at": starts,
            "capacity": cap,
            "rounds": rounds,
            "duration_minutes": dur,
        })
        game_ids.append(gid)
        print(f"Created Game #{gid}: {name} at '{venue}'")

    # 6. Student Game Choices & Enrollments
    # Aarav (0) takes game 0 and 2
    # Priya (1) takes game 0 and 3
    # Rohan (2) takes game 1 and 4
    # Ananya (3) takes game 1 and 6
    database.enroll(student_ids[0], [game_ids[0], game_ids[2]])
    database.enroll(student_ids[1], [game_ids[0], game_ids[3]])
    database.enroll(student_ids[2], [game_ids[1], game_ids[4]])
    database.enroll(student_ids[3], [game_ids[1], game_ids[6]])
    print("Enrolled students in games.")

    # 7. Record results for Game 0 (Cricket) and Game 1 (Basketball)
    # Cricket participants: student 0 and student 1
    # Basketball participants: student 2 and student 3
    all_participants = database.participants()
    game0_parts = [p for p in all_participants if p["game_id"] == game_ids[0]]
    if len(game0_parts) >= 2:
        database.record_results(
            game_ids[0],
            1,
            [
                {"participant_id": game0_parts[0]["id"], "score": 85, "status": "played", "placement": 1},
                {"participant_id": game0_parts[1]["id"], "score": 62, "status": "played", "placement": 2},
            ],
            admin_user["id"],
        )
        print("Recorded results for Game #1.")

    game1_parts = [p for p in all_participants if p["game_id"] == game_ids[1]]
    if len(game1_parts) >= 2:
        database.record_results(
            game_ids[1],
            1,
            [
                {"participant_id": game1_parts[0]["id"], "score": 21, "status": "played", "placement": 1},
                {"participant_id": game1_parts[1]["id"], "score": 19, "status": "played", "placement": 2},
            ],
            admin_user["id"],
        )
        print("Recorded results for Game #2.")

    print("\nDatabase successfully seeded with realistic live production data!")

if __name__ == "__main__":
    seed()
