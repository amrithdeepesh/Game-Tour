"""
Live Testing Agency Audit Script
Comprehensive test verifying all requirements as a real admin user and real student:
- Faction dropdown management & validation
- 8-character password enforcement
- 7 allowed game locations dropdown validation & rejection of any other location
- Student removal from Faction Management roster
- Complete Phase 1 to Phase 4 Data Structures & Algorithms verification
"""

import json
import os
import sys
import unittest
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

# Add backend to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import database
from algorithms.expression_handler import evaluate_simple_expression, evaluate_expression_detailed
from algorithms.search_sort import linear_search_detailed, binary_search_detailed, merge_sort_detailed
from algorithms.problem_solver import schedule_maximum_matches
from data_structures.linked_list import LinkedList
from data_structures.stack import Stack
from data_structures.queue import Queue
from data_structures.tree import BinarySearchTree
from data_structures.graph import Graph

BASE_URL = "http://127.0.0.1:8000"
ALLOWED_VENUES = [
    "Cricket Ground",
    "Basketball Court",
    "Volleyball Court",
    "Badminton Court",
    "Indoor Sports Complex",
    "Tennis Court",
    "Athletics Track",
]


class LiveClient:
    def __init__(self):
        self.cj = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def request(self, path, method="GET", data=None):
        url = BASE_URL + path
        headers = {"Origin": "http://localhost:3000"}
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with self.opener.open(req) as resp:
                resp_body = resp.read().decode("utf-8")
                return resp.status, json.loads(resp_body) if resp_body else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                parsed = json.loads(err_body)
            except Exception:
                parsed = {"error": err_body}
            return e.code, parsed


class TestAgencyComprehensiveAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Clean test state: truncate tables and ensure admin & factions are provisioned
        c = database.connect()
        cur = c.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for t in [
            "result_audit", "results", "matches", "waiting_lists",
            "game_choices", "games", "tournaments", "sessions",
            "announcements", "factions", "users",
        ]:
            cur.execute(f"TRUNCATE TABLE {t};")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        c.commit()
        c.close()

        database._ready = False
        database.init()

    def test_01_factions_managed_by_admin_and_publicly_listed(self):
        """Verify factions list is available and contains admin-managed factions."""
        client = LiveClient()
        status, data = client.request("/api/factions")
        self.assertEqual(status, 200)
        self.assertIn("factions", data)
        faction_names = [f["name"] for f in data["factions"]]
        self.assertIn("Falcons", faction_names)
        self.assertIn("Tigers", faction_names)
        self.assertIn("Sharks", faction_names)
        self.assertIn("Eagles", faction_names)

    def test_02_student_registration_validation(self):
        """Verify student registration enforces admin-managed faction dropdown and 8-char password."""
        client = LiveClient()

        # Test A: Unmanaged / invalid faction must be rejected
        status, data = client.request("/api/register", "POST", {
            "name": "Invalid Faction User",
            "email": "invalid_faction@student.test",
            "username": "badfaction_user",
            "faction": "NonExistentFaction123",
            "password": "validPassword8",
        })
        self.assertIn(status, [400, 500])
        self.assertIn("faction", str(data).lower())

        # Test B: Password < 8 characters must be rejected
        status, data = client.request("/api/register", "POST", {
            "name": "Short Password User",
            "email": "short_pw@student.test",
            "username": "shortpw_user",
            "faction": "Falcons",
            "password": "short7!",
        })
        self.assertIn(status, [400, 500])
        self.assertIn("8", str(data))

        # Test C: Valid student registration with 8-character password and admin-managed faction
        status, data = client.request("/api/register", "POST", {
            "name": "Aarav Sharma",
            "email": "aarav@student.test",
            "username": "aarav_s",
            "faction": "Falcons",
            "password": "pass1234",  # Exactly 8 characters!
        })
        self.assertEqual(status, 201)
        self.assertTrue(data.get("created"))

        # Register additional students for tournament participation
        students_to_create = [
            ("Priya Nair", "priya@student.test", "priya_n", "Tigers", "pass1234"),
            ("Rohan Iyer", "rohan@student.test", "rohan_i", "Sharks", "pass1234"),
            ("Ananya Rao", "ananya@student.test", "ananya_r", "Eagles", "pass1234"),
            ("Temp Student", "temp@student.test", "temp_user", "Falcons", "pass1234"),
        ]
        for name, email, uname, fact, pw in students_to_create:
            s_client = LiveClient()
            st, res = s_client.request("/api/register", "POST", {
                "name": name,
                "email": email,
                "username": uname,
                "faction": fact,
                "password": pw,
            })
            self.assertEqual(st, 201, f"Failed to register {name}: {res}")

    def test_03_admin_game_location_dropdown_enforcement(self):
        """Verify admin can only add games with the 7 allowed locations and nothing else."""
        admin = LiveClient()
        pw = os.getenv("ADMIN_PASSWORD", "Din@pr@bh@7012760095")
        status, data = admin.request("/api/login", "POST", {
            "username": "admin1",
            "password": pw,
        })
        self.assertEqual(status, 200, f"Admin login failed: {data}")

        # Create tournament
        st, tourney = admin.request("/api/tournaments", "POST", {
            "name": "ARENA Campus Cup 2026",
            "description": "Annual multi-venue championship",
            "points_first": 10,
            "points_second": 7,
            "points_third": 5,
            "points_participation": 1,
        })
        self.assertEqual(st, 201)
        tournament_id = tourney["id"]

        # Attempt to create game with unauthorized location
        st, res = admin.request("/api/games", "POST", {
            "tournament_id": tournament_id,
            "name": "Illegal Location Game",
            "starts_at": "2026-11-01 10:00:00",
            "venue": "Unauthorized City Stadium",
            "capacity": 20,
            "rounds": 1,
            "duration_minutes": 60,
        })
        self.assertIn(st, [400, 500])
        self.assertIn("Location must be one of", str(res))

        # Successfully create games with each of the 7 allowed venues at distinct, non-overlapping times
        created_games = {}
        for idx, venue in enumerate(ALLOWED_VENUES):
            st, res = admin.request("/api/games", "POST", {
                "tournament_id": tournament_id,
                "name": f"{venue} Championship",
                "starts_at": f"2026-11-01 {9 + idx * 2:02d}:00:00",
                "venue": venue,
                "capacity": 30,
                "rounds": 1,
                "duration_minutes": 60,
            })
            self.assertEqual(st, 201, f"Failed to create game at {venue}: {res}")
            created_games[venue] = res["id"]

        self.assertEqual(len(created_games), 7)

    def test_04_student_choices_and_game_enrollment(self):
        """Verify student can sign in and submit game choices."""
        student = LiveClient()
        st, res = student.request("/api/login", "POST", {
            "username": "aarav_s",
            "password": "pass1234",
        })
        self.assertEqual(st, 200)

        # Get dashboard games
        st, dash = student.request("/api/dashboard")
        self.assertEqual(st, 200)
        game_ids = [g["id"] for g in dash["games"][:3]]
        self.assertTrue(len(game_ids) > 0)

        # Submit game choices
        st, choice_res = student.request("/api/choices", "POST", {"game_ids": game_ids})
        self.assertEqual(st, 201)

    def test_05_admin_remove_student_account_from_faction_roster(self):
        """Verify admin can remove a student account completely from Faction Management."""
        admin = LiveClient()
        pw = os.getenv("ADMIN_PASSWORD", "Din@pr@bh@7012760095")
        admin.request("/api/login", "POST", {"username": "admin1", "password": pw})

        # Find the temp_user student
        st, sdata = admin.request("/api/students")
        self.assertEqual(st, 200)
        temp_student = next((s for s in sdata["students"] if s["username"] == "temp_user"), None)
        self.assertIsNotNone(temp_student, "temp_user was not found in students list")

        # Admin permanently deletes student account
        st, del_res = admin.request(f"/api/participants/{temp_student['id']}", "DELETE")
        self.assertEqual(st, 200)
        self.assertTrue(del_res.get("deleted"))

        # Verify student is removed from database
        st, sdata_after = admin.request("/api/students")
        remaining_unames = [s["username"] for s in sdata_after["students"]]
        self.assertNotIn("temp_user", remaining_unames)

        # Verify deleted student cannot log in
        dead_client = LiveClient()
        st, _ = dead_client.request("/api/login", "POST", {"username": "temp_user", "password": "pass1234"})
        self.assertIn(st, [400, 401, 500])

    def test_06_phase_1_data_structures(self):
        """Phase 1: Singly Linked List (insert, delete, traverse), Stack, Queue, Expression Handler."""
        # 1. Singly Linked List
        ll = LinkedList()
        ll.insert_at_start({"student_id": "S1", "name": "Aarav"})
        ll.insert_at_end({"student_id": "S2", "name": "Priya"})
        ll.insert_at_position(1, {"student_id": "S3", "name": "Rohan"})
        nodes = ll.traverse()
        self.assertEqual([n["student_id"] for n in nodes], ["S1", "S3", "S2"])

        # Delete operations
        ll.delete_by_student_id("S3")
        self.assertEqual([n["student_id"] for n in ll.traverse()], ["S1", "S2"])
        ll.delete_at_position(0)
        self.assertEqual([n["student_id"] for n in ll.traverse()], ["S2"])

        # 2. Stack using Linked List
        st = Stack()
        self.assertTrue(st.is_empty())
        st.push("Score 10")
        st.push("Score 20")
        self.assertEqual(st.peek(), "Score 20")
        self.assertEqual(st.pop(), "Score 20")
        self.assertEqual(st.pop(), "Score 10")
        self.assertTrue(st.is_empty())

        # 3. Queue using Linked List
        q = Queue()
        self.assertTrue(q.is_empty())
        q.enqueue("Player A")
        q.enqueue("Player B")
        self.assertEqual(q.peek(), "Player A")
        self.assertEqual(q.dequeue(), "Player A")
        self.assertEqual(q.dequeue(), "Player B")
        self.assertTrue(q.is_empty())

        # 4. Simple expression handling using stack
        self.assertEqual(evaluate_simple_expression("1200 + 40 * 2"), 1280)
        self.assertEqual(evaluate_simple_expression("(10 + 5) * 4"), 60)
        detailed = evaluate_expression_detailed("25 + 5 * 2")
        self.assertEqual(detailed["result"], 35)
        self.assertTrue(len(detailed["evaluation_steps"]) > 0)

    def test_07_phase_2_hierarchical_and_graph_structures(self):
        """Phase 2: Binary Tree / BST, Traversals (inorder, preorder, postorder), Graph BFS."""
        # 1. BST & Traversals
        bst = BinarySearchTree()
        values = [50, 30, 70, 20, 40, 60, 80]
        for v in values:
            bst.insert(v)

        self.assertEqual(bst.inorder(), [20, 30, 40, 50, 60, 70, 80])
        self.assertEqual(bst.preorder(), [50, 30, 20, 40, 70, 60, 80])
        self.assertEqual(bst.postorder(), [20, 40, 30, 60, 80, 70, 50])
        self.assertTrue(bst.contains(40))
        self.assertFalse(bst.contains(999))
        self.assertEqual(bst.find_min(), 20)
        self.assertEqual(bst.find_max(), 80)

        # 2. Basic Graph Representation & BFS Traversal with 7 Allowed Venues
        g = Graph(ALLOWED_VENUES)
        edges = [
            ("Indoor Sports Complex", "Cricket Ground"),
            ("Indoor Sports Complex", "Athletics Track"),
            ("Indoor Sports Complex", "Basketball Court"),
            ("Indoor Sports Complex", "Volleyball Court"),
            ("Indoor Sports Complex", "Badminton Court"),
            ("Indoor Sports Complex", "Tennis Court"),
            ("Cricket Ground", "Athletics Track"),
            ("Basketball Court", "Volleyball Court"),
            ("Volleyball Court", "Badminton Court"),
            ("Badminton Court", "Tennis Court"),
            ("Athletics Track", "Tennis Court"),
        ]
        for u, v in edges:
            g.add_edge(u, v)

        bfs_traversal = g.bfs("Indoor Sports Complex")
        self.assertEqual(bfs_traversal[0], "Indoor Sports Complex")
        self.assertEqual(len(bfs_traversal), 7)
        for venue in ALLOWED_VENUES:
            self.assertIn(venue, bfs_traversal)

        # Live Graph API endpoint check
        client = LiveClient()
        st, gdata = client.request("/api/ds-lab/phase2/graph", "POST", {"start": "Indoor Sports Complex"})
        self.assertEqual(st, 200)
        self.assertEqual(gdata["start"], "Indoor Sports Complex")
        self.assertEqual(len(gdata["venues"]), 7)

    def test_08_phase_3_search_and_sort_algorithms(self):
        """Phase 3: Linear search, Binary search, and Merge sort."""
        athletes = [
            {"id": 1, "name": "Aarav", "points": 45},
            {"id": 2, "name": "Ananya", "points": 85},
            {"id": 3, "name": "Priya", "points": 60},
            {"id": 4, "name": "Rohan", "points": 30},
            {"id": 5, "name": "Vikram", "points": 90},
        ]

        # 1. Linear Search
        lin_res = linear_search_detailed(athletes, "Priya", "name")
        self.assertTrue(lin_res["found"])
        self.assertEqual(lin_res["item"]["name"], "Priya")

        # 2. Binary Search (requires sorted list by search field)
        sorted_by_name = sorted(athletes, key=lambda x: x["name"])
        bin_res = binary_search_detailed(sorted_by_name, "Rohan", "name")
        self.assertTrue(bin_res["found"])
        self.assertEqual(bin_res["item"]["name"], "Rohan")

        # 3. Merge Sort
        sort_res = merge_sort_detailed(athletes, "points", descending=True)
        sorted_points = [x["points"] for x in sort_res["sorted"]]
        self.assertEqual(sorted_points, [90, 85, 60, 45, 30])

    def test_09_phase_4_greedy_technique_and_application_integration(self):
        """Phase 4: Greedy Interval Scheduling and application flow integration."""
        intervals = [
            {"name": "100m Heats", "start": 9.0, "end": 10.5},
            {"name": "Cricket Derby", "start": 10.0, "end": 12.0},
            {"name": "Basketball Semis", "start": 10.5, "end": 11.5},
            {"name": "Volleyball Finals", "start": 11.5, "end": 13.0},
            {"name": "Badminton Masters", "start": 12.0, "end": 14.0},
            {"name": "Grand Finals", "start": 13.0, "end": 15.0},
        ]
        # Greedy algorithm: earliest finish time
        scheduled = schedule_maximum_matches(intervals)
        self.assertTrue(len(scheduled) >= 3)
        # Ensure non-overlapping property
        for i in range(len(scheduled) - 1):
            self.assertLessEqual(scheduled[i]["end"], scheduled[i + 1]["start"])

        # Live demo endpoint integrating all custom structures into application flow
        client = LiveClient()
        st, demo = client.request("/api/demo")
        self.assertEqual(st, 200)
        self.assertIn("linkedList", demo)
        self.assertIn("stackActions", demo)
        self.assertIn("queueItems", demo)
        self.assertIn("tree", demo)
        self.assertIn("graph", demo)
        self.assertEqual(demo["graph"]["bfs"][0], "Indoor Sports Complex")
        self.assertIn("greedySchedule", demo)


if __name__ == "__main__":
    unittest.main()
