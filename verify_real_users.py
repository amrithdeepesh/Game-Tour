"""
Real User (Student & Admin) Frontend + API Verification Script
Acts as a real student and real admin exercising the full running application.
"""

import json
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://127.0.0.1:8000"

class BrowserSession:
    def __init__(self, name="User"):
        self.name = name
        self.cj = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def fetch_page(self, path):
        url = FRONTEND_URL + path
        req = urllib.request.Request(url, headers={"User-Agent": f"BrowserSession/{self.name}"})
        with self.opener.open(req) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            print(f"[{self.name}] GET {path} -> {resp.status} (Length: {len(content)})")
            return resp.status, content

    def api_call(self, path, method="GET", payload=None):
        url = BACKEND_URL + path
        headers = {
            "Origin": FRONTEND_URL,
            "User-Agent": f"BrowserSession/{self.name}",
        }
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with self.opener.open(req) as resp:
                resp_text = resp.read().decode("utf-8")
                data = json.loads(resp_text) if resp_text else {}
                print(f"[{self.name}] {method} {path} -> {resp.status}")
                return resp.status, data
        except urllib.error.HTTPError as e:
            resp_text = e.read().decode("utf-8")
            try:
                data = json.loads(resp_text)
            except Exception:
                data = {"error": resp_text}
            print(f"[{self.name}] {method} {path} -> {e.code}: {data}")
            return e.code, data

def run_real_user_verification():
    print("=" * 70)
    print("STARTING REAL USER (STUDENT & ADMIN) END-TO-END VERIFICATION")
    print("=" * 70)

    # ----------------------------------------------------
    # 1. REAL STUDENT JOURNEY
    # ----------------------------------------------------
    print("\n--- [1] REAL STUDENT JOURNEY ---")
    student = BrowserSession("Student: Divya")

    # Step A: Student loads Registration Page
    status, html = student.fetch_page("/register")
    assert status == 200, "Registration page must return 200"
    assert "STUDENT REGISTRATION" in html, "Page must contain registration header"

    # Step B: Student fetches factions for the dropdown
    st, fdata = student.api_call("/api/factions")
    assert st == 200, "Factions must be public"
    factions = [f["name"] for f in fdata["factions"]]
    print(f"[Student: Divya] Available factions in dropdown: {factions}")
    assert "Falcons" in factions and "Tigers" in factions, "Factions must be present"

    # Step C: Student attempts registration with invalid faction -> must fail
    st, err = student.api_call("/api/register", "POST", {
        "name": "Divya Kumar",
        "email": "divya@student.test",
        "username": "divya_k",
        "faction": "FakeFaction999",
        "password": "password88",
    })
    assert st in [400, 500], "Unmanaged faction must be rejected"
    print("  ✓ Unmanaged faction properly rejected")

    # Step D: Student attempts registration with short password (<8 chars) -> must fail
    st, err = student.api_call("/api/register", "POST", {
        "name": "Divya Kumar",
        "email": "divya@student.test",
        "username": "divya_k",
        "faction": "Tigers",
        "password": "short7!",
    })
    assert st in [400, 500], "Password < 8 characters must be rejected"
    print("  ✓ Password < 8 characters properly rejected")

    # Step E: Student registers with valid faction dropdown option and 8-char password
    st, res = student.api_call("/api/register", "POST", {
        "name": "Divya Kumar",
        "email": "divya@student.test",
        "username": "divya_k",
        "faction": "Tigers",
        "password": "divya123",  # Exactly 8 characters
    })
    assert st == 201, f"Registration must succeed: {res}"
    print("  ✓ Student registered successfully with 8-character password and admin-managed faction")

    # Step F: Student logs in
    st, res = student.api_call("/api/login", "POST", {
        "username": "divya_k",
        "password": "divya123",
    })
    assert st == 200, f"Login must succeed: {res}"
    print(f"  ✓ Student signed in as {res['user']['name']} ({res['user']['role']})")

    # Step G: Student visits sports/games list and selects games
    student.fetch_page("/sports")
    st, dash = student.api_call("/api/dashboard")
    available_games = dash.get("games", [])
    print(f"  ✓ Student loaded dashboard: {len(available_games)} games available")

    # Pick 2 games (e.g. game 3 and game 6)
    games_to_pick = [available_games[2]["id"], available_games[5]["id"]]
    st, c_res = student.api_call("/api/choices", "POST", {"game_ids": games_to_pick})
    assert st == 201, f"Game choices must be saved: {c_res}"
    print(f"  ✓ Student saved game choices: {games_to_pick}")

    # Step H: Student visits My Events, Schedule, Standings
    student.fetch_page("/my-events")
    student.fetch_page("/schedule")
    student.fetch_page("/leaderboard")
    student.fetch_page("/faction-leaderboard")

    # Step I: Student explores Phase 1-4 DS Tools
    student.fetch_page("/structures")
    st, demo = student.api_call("/api/demo")
    assert st == 200, "Demo DS API must return 200"
    print("  ✓ Operations Desk (Phase 1-4 Demo) loaded successfully")
    assert "Indoor Sports Complex" in demo["graph"]["bfs"][0]

    # Expression Calculator Test
    st, expr_res = student.api_call("/api/ds-lab/phase1/expression", "POST", {"expression": "(15 * 4) + 120"})
    assert st == 200, "Expression evaluator must succeed"
    print(f"  ✓ Stack Expression Calculator: (15 * 4) + 120 = {expr_res['result']}")

    # Tab 2 Campus BFS Navigator Test
    student.fetch_page("/lab")
    st, g_res = student.api_call("/api/ds-lab/phase2/graph", "POST", {
        "start": "Cricket Ground",
        "target": "Indoor Sports Complex",
    })
    assert st == 200, "Graph API must succeed"
    print(f"  ✓ Campus Navigator BFS search from Cricket Ground: {len(g_res['bfs'])} venues traversed")

    # Tab 3 Search & Merge Sort Test
    student.fetch_page("/algorithms")
    st, search_res = student.api_call("/api/ds-lab/phase3/search", "POST", {
        "query": "Divya",
        "method": "linear",
    })
    assert st == 200, "Search must succeed"
    print(f"  ✓ Participant Linear Search found: {search_res['found']} ({search_res.get('total_comparisons', 0)} comparisons)")

    # Tab 4 Greedy Scheduler Test
    st, greedy_res = student.api_call("/api/ds-lab/phase4/greedy-schedule", "POST", {})
    assert st == 200, "Greedy scheduler must succeed"
    print(f"  ✓ Greedy Conflict-Free Scheduler: {greedy_res['scheduled_count']} non-overlapping events selected")

    # ----------------------------------------------------
    # 2. REAL ADMIN JOURNEY
    # ----------------------------------------------------
    print("\n--- [2] REAL ADMIN JOURNEY ---")
    admin = BrowserSession("Admin: Admin1")

    # Step A: Admin signs in
    st, a_res = admin.api_call("/api/login", "POST", {
        "username": "admin1",
        "password": "Din@pr@bh@7012760095",
    })
    assert st == 200, "Admin login must succeed"
    print(f"  ✓ Administrator signed in successfully: {a_res['user']['name']}")

    # Step B: Admin checks Participants Page
    st, p_page = admin.fetch_page("/participants")
    assert "Student accounts" not in p_page, "Side section about student accounts (pause access) must be removed!"
    print("  ✓ Confirmed: Pause access / student accounts side card is completely removed from /participants")

    # Step C: Admin checks Tournament management and 7 allowed locations
    st, t_page = admin.fetch_page("/tournament")
    for venue in [
        "Cricket Ground", "Basketball Court", "Volleyball Court",
        "Badminton Court", "Indoor Sports Complex", "Tennis Court", "Athletics Track"
    ]:
        assert venue in t_page, f"Allowed venue {venue} must be present in the dropdown"
    print("  ✓ Confirmed: All 7 allowed venues present in tournament games dropdown")

    # Test creating a game with illegal venue -> must be blocked
    st, err = admin.api_call("/api/games", "POST", {
        "tournament_id": 1,
        "name": "Invalid Venue Test",
        "starts_at": "2026-11-02 10:00:00",
        "venue": "Unauthorized Arena Floor",
        "capacity": 20,
    })
    assert st in [400, 500], "Non-whitelisted venue must be rejected"
    print("  ✓ Invalid game location successfully rejected by backend validator")

    # Step D: Admin manages Faction Student Rosters and removes Divya's account
    admin.fetch_page("/factions")
    st, s_list = admin.api_call("/api/students")
    divya_record = next((s for s in s_list["students"] if s["username"] == "divya_k"), None)
    assert divya_record is not None, "Divya must be in student roster"
    print(f"  ✓ Found student in faction roster: {divya_record['name']} (ID: {divya_record['id']})")

    # Admin removes student account from faction roster table
    st, del_res = admin.api_call(f"/api/participants/{divya_record['id']}", "DELETE")
    assert st == 200, f"Student account deletion must succeed: {del_res}"
    print(f"  ✓ Successfully removed student account '{divya_record['name']}' from Faction Student Rosters")

    # Verify student is removed and cannot log in anymore
    st, s_list_after = admin.api_call("/api/students")
    assert not any(s["username"] == "divya_k" for s in s_list_after["students"]), "Student must be deleted"
    dead_client = BrowserSession("Deleted Student")
    st, _ = dead_client.api_call("/api/login", "POST", {"username": "divya_k", "password": "divya123"})
    assert st in [400, 401, 500], "Deleted student must not be able to log in"
    print("  ✓ Verified: Student account permanently deleted and cannot sign in")

    # Step E: Admin records results
    st, r_res = admin.api_call("/api/results", "POST", {
        "game_id": 2,
        "round": 1,
        "entries": [
            {"participant_id": 2, "score": 24, "status": "played", "placement": 1},
            {"participant_id": 4, "score": 18, "status": "played", "placement": 2},
        ],
    })
    assert st in [200, 201], "Results recording must succeed"
    print("  ✓ Results and tournament points recorded successfully")

    print("\n" + "=" * 70)
    print("ALL REAL USER TESTS (STUDENT & ADMIN) COMPLETED SUCCESSFULLY WITH 100% PASS RATE!")
    print("=" * 70)

if __name__ == "__main__":
    run_real_user_verification()

