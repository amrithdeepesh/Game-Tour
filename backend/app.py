"""Tournament API with role sessions and integrated operations algorithms."""

import hashlib
import ipaddress
import json
import os
import re
import secrets
import socket
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import mysql.connector

import database
from algorithms.expression_handler import (
    evaluate_simple_expression,
    evaluate_expression_detailed,
)
from algorithms.problem_solver import (
    schedule_maximum_matches,
    schedule_tournament_events,
)
from algorithms.search_sort import (
    binary_search,
    linear_search,
    merge_sort,
    selection_sort,
    linear_search_detailed,
    binary_search_detailed,
    merge_sort_detailed,
    benchmark_search_sort,
)
from data_structures.graph import Graph
from data_structures.linked_list import LinkedList
from data_structures.queue import Queue
from data_structures.stack import Stack
from data_structures.tree import BinarySearchTree, TournamentBinaryTree


def _allowed_frontend_origin(origin):
    if not origin:
        return False
    configured = {
        x.strip().rstrip("/")
        for x in os.getenv("FRONTEND_ORIGINS", "").split(",")
        if x.strip()
    }
    if origin.rstrip("/") in configured:
        return True
    try:
        parsed = urlparse(origin)
        if (
            parsed.scheme != "http"
            or parsed.port not in (3000, 3001)
            or not parsed.hostname
        ):
            return False
        host = parsed.hostname.lower().rstrip(".")
        return host in ("localhost", "127.0.0.1", "::1", socket.gethostname().lower())
    except (ValueError, TypeError):
        return False


ALLOWED_VENUES = (
    "Cricket Ground",
    "Basketball Court",
    "Volleyball Court",
    "Badminton Court",
    "Indoor Sports Complex",
    "Tennis Court",
    "Athletics Track",
)


_LOGIN_FAILURES = {}
_LOGIN_LOCK = threading.Lock()


def _login_blocked(key):
    now = time.monotonic()
    with _LOGIN_LOCK:
        attempts = [t for t in _LOGIN_FAILURES.get(key, []) if now - t < 900]
        _LOGIN_FAILURES[key] = attempts
        return len(attempts) >= 5


def _login_failed(key):
    now = time.monotonic()
    with _LOGIN_LOCK:
        attempts = [t for t in _LOGIN_FAILURES.get(key, []) if now - t < 900]
        attempts.append(now)
        _LOGIN_FAILURES[key] = attempts


def _login_succeeded(key):
    with _LOGIN_LOCK:
        _LOGIN_FAILURES.pop(key, None)


def password_hash(password):
    salt = secrets.token_bytes(16)
    return (
        salt.hex()
        + ":"
        + hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240000).hex()
    )


def password_ok(password, saved):
    try:
        salt, key = saved.split(":")
        return secrets.compare_digest(
            hashlib.pbkdf2_hmac(
                "sha256", password.encode(), bytes.fromhex(salt), 240000
            ).hex(),
            key,
        )
    except:
        return False


def player_rows():
    return [
        {
            "student_id": str(r["user_id"]),
            "name": r["display_name"],
            "faction": r["faction"],
            "points": r["points"],
            "wins": r["first_places"],
            "game": "All tournaments",
        }
        for r in database.leaderboard()
    ]


def scheduled_rows(games):
    rows = []
    for g in games:
        dt = g["starts_at"]
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        start = (
            dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        ).timestamp()
        rows.append(
            {
                "name": g["name"],
                "start": start,
                "end": start + max(1, int(g.get("duration_minutes", 60))) * 60,
            }
        )
    return rows


def phase_demo():
    # The same data records used by registration and game choices are loaded into
    # the linked-list demo, so the visualization is backed by the real structure.
    linked = LinkedList()
    for entry in database.choices():
        linked.insert_at_end(
            {
                "student_id": "ST" + str(entry["user_id"]),
                "name": entry["display_name"],
                "game": entry["game"],
            }
        )

    players = player_rows()
    values = [player["points"] for player in players if player["points"] > 0] or [
        20,
        40,
        60,
        80,
        100,
    ]
    tree = BinarySearchTree()
    for value in values:
        tree.insert(value)

    action_stack = Stack()
    for action in ("Student registered", "Game choice submitted", "Score recorded"):
        action_stack.push(action)
    check_in_queue = Queue()
    for match in ("Next match check-in", "Following match check-in"):
        check_in_queue.enqueue(match)

    venues = Graph(ALLOWED_VENUES)
    for first, second in (
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
    ):
        venues.add_edge(first, second)

    intervals = scheduled_rows(database.games())
    return {
        "linkedList": linked.traverse(),
        "stackTop": action_stack.peek(),
        "stackActions": action_stack.to_list(),
        "queueFront": check_in_queue.peek(),
        "queueItems": check_in_queue.to_list(),
        "tree": {
            "inorder": tree.inorder(),
            "preorder": tree.preorder(),
            "postorder": tree.postorder(),
            "searchValue": values[-1],
            "searchFound": tree.contains(values[-1]),
        },
        "graph": {"bfs": venues.bfs("Indoor Sports Complex"), "dfs": venues.dfs("Indoor Sports Complex")},
        "greedySchedule": schedule_maximum_matches(intervals),
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200, extra=None):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        origin = self.headers.get("Origin")
        if _allowed_frontend_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        for k, v in extra or []:
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def payload(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except (TypeError, ValueError):
            raise ValueError("Invalid request length.")
        if length < 0 or length > 1048576:
            raise ValueError("Request is too large.")
        if (
            length
            and "application/json" not in self.headers.get("Content-Type", "").lower()
        ):
            raise ValueError("Send the form as JSON.")
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("Request data is not valid JSON.")
        if not isinstance(data, dict):
            raise ValueError("Request data must be an object.")
        return data

    def require_trusted_origin(self):
        origin = self.headers.get("Origin")
        if not origin or not _allowed_frontend_origin(origin):
            raise PermissionError("This website origin is not allowed.")

    def user(self):
        token = next(
            (
                x.split("=", 1)[1]
                for x in self.headers.get("Cookie", "").split("; ")
                if x.startswith("arena_session=")
            ),
            None,
        )
        return (
            database.session_user(hashlib.sha256(token.encode()).hexdigest())
            if token
            else None
        )

    def need(self, role=None):
        u = self.user()
        if not u:
            raise PermissionError("Please sign in to continue.")
        if role and u["role"] != role:
            raise PermissionError("This action is available to administrators only.")
        return u

    def error(self, e):
        if isinstance(e, PermissionError):
            return self.send_json({"error": str(e)}, 401)
        if isinstance(e, ValueError):
            return self.send_json({"error": str(e)}, 400)
        if isinstance(e, mysql.connector.IntegrityError):
            return self.send_json(
                {
                    "error": "That account or record already exists, or its details are invalid."
                },
                409,
            )
        if isinstance(e, (RuntimeError, mysql.connector.Error)):
            return self.send_json(
                {
                    "error": (
                        str(e)
                        if isinstance(e, RuntimeError)
                        else "MySQL is unavailable. Check backend/.env and the local MySQL service."
                    )
                },
                503,
            )
        return self.send_json(
            {
                "error": "Could not complete this request: " + str(e)
            },
            500,
        )

    def do_OPTIONS(self):
        self.send_json({})

    def do_PUT(self):
        path = urlparse(self.path).path
        try:
            self.require_trusted_origin()
            data = self.payload()
            self.need("admin")
            if path.startswith("/api/participants/") and path.endswith("/status"):
                participant_id = int(path.split("/")[-2])
                database.set_participant_active(
                    participant_id, bool(data.get("active"))
                )
                return self.send_json({"saved": True})
            if path.startswith("/api/tournaments/"):
                database.update_tournament(int(path.rsplit("/", 1)[1]), data)
                return self.send_json({"saved": True})
            if path.startswith("/api/games/"):
                if "venue" in data:
                    venue = str(data.get("venue", "")).strip()
                    if venue not in ALLOWED_VENUES:
                        raise ValueError(f"Location must be one of: {', '.join(ALLOWED_VENUES)}.")
                database.update_game(int(path.rsplit("/", 1)[1]), data)
                return self.send_json({"saved": True})
            if path.startswith("/api/matches/"):
                if "venue" in data:
                    venue = str(data.get("venue", "")).strip()
                    if venue and venue not in ALLOWED_VENUES:
                        raise ValueError(f"Location must be one of: {', '.join(ALLOWED_VENUES)}.")
                match_id = int(path.rsplit("/", 1)[1])
                database.update_match(match_id, data)
                return self.send_json({"saved": True})
            if path.startswith("/api/factions/"):
                faction_id = int(path.rsplit("/", 1)[1])
                database.update_faction(faction_id, data)
                return self.send_json({"saved": True})
            return self.send_json({"error": "Not found"}, 404)
        except Exception as e:
            return self.error(e)

    def do_DELETE(self):
        path = urlparse(self.path).path
        try:
            self.require_trusted_origin()
            u = self.need()
            if path.startswith("/api/tournaments/"):
                self.need("admin")
                database.delete_tournament(int(path.rsplit("/", 1)[1]))
                return self.send_json({"deleted": True})
            if path.startswith("/api/games/"):
                self.need("admin")
                database.delete_game(int(path.rsplit("/", 1)[1]))
                return self.send_json({"deleted": True})
            if path.startswith("/api/participants/") or path.startswith("/api/students/"):
                self.need("admin")
                database.delete_participant(int(path.rsplit("/", 1)[1]))
                return self.send_json({"deleted": True})
            if path.startswith("/api/waiting-list/"):
                wid = int(path.rsplit("/", 1)[1])
                if u["role"] == "admin":
                    database.mutate("DELETE FROM waiting_lists WHERE id=%s", (wid,))
                else:
                    database.mutate(
                        "DELETE FROM waiting_lists WHERE id=%s AND user_id=%s",
                        (wid, u["id"]),
                    )
                return self.send_json({"deleted": True})
            return self.send_json({"error": "Not found"}, 404)
        except Exception as e:
            return self.error(e)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        params = parse_qs(parsed_url.query)
        try:
            if path == "/api/health":
                database.init()
                return self.send_json({"ok": True, "database": "mysql"})
            if path == "/api/me":
                return self.send_json({"user": self.user()})
            if path == "/api/logout":
                u = self.user()
                cookie = self.headers.get("Cookie", "")
                token = next(
                    (
                        x.split("=", 1)[1]
                        for x in cookie.split("; ")
                        if x.startswith("arena_session=")
                    ),
                    None,
                )
                if u and token:
                    database.delete_session(hashlib.sha256(token.encode()).hexdigest())
                return self.send_json(
                    {"ok": True},
                    200,
                    [
                        (
                            "Set-Cookie",
                            "arena_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0",
                        )
                    ],
                )
            if path == "/api/factions":
                return self.send_json({"factions": database.factions()})
            if path == "/api/demo":
                return self.send_json(phase_demo())
            if path == "/api/ds-lab/benchmark":
                return self.send_json(benchmark_search_sort())
            u = self.need()
            if path == "/api/dashboard":
                gs = database.games()
                mine = database.choices(u["id"]) if u["role"] == "student" else []
                leaders = player_rows()
                all_choices = database.choices()
                active_matches = database.matches(status="ongoing")
                upcoming_matches = database.matches(status="upcoming")
                factions_data = database.factions()
                announcements_data = database.announcements()
                my_waiting = database.waiting_list(user_id=u["id"]) if u["role"] == "student" else []
                return self.send_json(
                    {
                        "user": u,
                        "tournaments": database.tournaments(),
                        "games": gs,
                        "my_games": mine,
                        "my_waiting": my_waiting,
                        "choices": all_choices if u["role"] == "admin" else [],
                        "players": leaders,
                        "matches": scheduled_rows(gs),
                        "live_matches": active_matches,
                        "upcoming_matches": upcoming_matches,
                        "factions": factions_data,
                        "announcements": announcements_data,
                        "stats": {
                            "tournaments": len(database.tournaments()),
                            "games": len(gs),
                            "students": len(
                                database.query(
                                    "SELECT id FROM users WHERE role='student' AND is_active=1"
                                )
                            ),
                            "enrolled": len(all_choices),
                            "factions": len(factions_data),
                            "ongoing_matches": len(active_matches),
                        },
                    }
                )
            if path == "/api/games":
                return self.send_json({"games": database.games()})
            if path == "/api/tournaments":
                return self.send_json({"tournaments": database.tournaments()})
            if path == "/api/waiting-list":
                gid = params.get("game_id", [None])[0]
                uid = params.get("user_id", [None])[0]
                if u["role"] == "student" and not uid:
                    uid = u["id"]
                return self.send_json({"waiting_list": database.waiting_list(gid, uid)})
            if path == "/api/matches":
                gid = params.get("game_id", [None])[0]
                st = params.get("status", [None])[0]
                return self.send_json({"matches": database.matches(gid, st)})
            if path == "/api/announcements":
                return self.send_json({"announcements": database.announcements()})
            if path == "/api/choices":
                return self.send_json(
                    {
                        "choices": database.choices(
                            None if u["role"] == "admin" else u["id"]
                        )
                    }
                )
            if path.startswith("/api/game-leaderboard/"):
                game_id = int(path.rsplit("/", 1)[1])
                return self.send_json({"leaders": database.game_leaderboard(game_id)})
            tournament_id = params.get("tournament_id", [None])[0]
            if path == "/api/leaderboard":
                return self.send_json(
                    {
                        "leaders": database.leaderboard(
                            tournament_id=int(tournament_id) if tournament_id else None
                        )
                    }
                )
            if path == "/api/faction-leaderboard":
                return self.send_json(
                    {
                        "leaders": database.leaderboard(
                            True, int(tournament_id) if tournament_id else None
                        )
                    }
                )
            if path == "/api/participants":
                self.need("admin")
                return self.send_json({"participants": database.participants()})
            if path == "/api/students":
                self.need("admin")
                return self.send_json({"students": database.students()})
            if path == "/api/results/audit":
                self.need("admin")
                game_id = int(params.get("game_id", ["0"])[0])
                return self.send_json({"audit": database.result_audit(game_id)})
            if path == "/api/results":
                self.need("admin")
                game_id = params.get("game_id", [None])[0]
                round_no = params.get("round", [None])[0]
                return self.send_json(
                    {
                        "results": database.results(
                            int(game_id) if game_id else None,
                            int(round_no) if round_no else None,
                        )
                    }
                )
            return self.send_json({"error": "Not found"}, 404)
        except Exception as e:
            return self.error(e)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            self.require_trusted_origin()
            data = self.payload()
            if path == "/api/register":
                username = str(data.get("username", "")).strip().lower()
                email = str(data.get("email", "")).strip().lower()
                name = str(data.get("name", "")).strip()
                faction = str(data.get("faction", "")).strip()
                pw = str(data.get("password", ""))
                if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,39}", username):
                    raise ValueError(
                        "Use 3–40 letters, numbers, dots, underscores, or hyphens for the username."
                    )
                if len(email) > 254 or not re.fullmatch(
                    r"[^\s@]+@[^\s@]+\.[^\s@]+", email
                ):
                    raise ValueError("Enter a valid email address.")
                if not name or len(name) > 120 or not faction or len(faction) > 80:
                    raise ValueError(
                        "Name and faction are required and must fit the allowed length."
                    )
                valid_factions = {f["name"].strip().lower(): f["name"] for f in database.factions()}
                if not valid_factions:
                    raise ValueError("No active factions are configured by the administrator.")
                if faction.lower() not in valid_factions:
                    raise ValueError(f"Please select a valid faction managed by the administrator.")
                faction = valid_factions[faction.lower()]
                if not 8 <= len(pw) <= 128:
                    raise ValueError("Use a password between 8 and 128 characters.")
                database.create_user(
                    {
                        "username": username,
                        "email": email,
                        "name": name,
                        "faction": faction,
                    },
                    password_hash(pw),
                )
                return self.send_json({"created": True}, 201)
            if path == "/api/login":
                username = str(data.get("username", "")).strip().lower()
                password = str(data.get("password", ""))
                key = (self.client_address[0], username)
                if _login_blocked(key):
                    return self.send_json(
                        {
                            "error": "Too many sign-in attempts. Try again in 15 minutes."
                        },
                        429,
                    )
                row = database.user_by_username(username)
                if not row or not password_ok(password, row["password_hash"]):
                    _login_failed(key)
                    return self.send_json(
                        {"error": "Username or password is incorrect."}, 401
                    )
                _login_succeeded(key)
                token = secrets.token_urlsafe(32)
                database.save_session(
                    hashlib.sha256(token.encode()).hexdigest(),
                    row["id"],
                    datetime.utcnow() + timedelta(days=7),
                )
                secure = (
                    "; Secure"
                    if os.getenv("COOKIE_SECURE", "").lower() in ("1", "true", "yes")
                    else ""
                )
                return self.send_json(
                    {"user": database.user_by_id(row["id"])},
                    200,
                    [
                        (
                            "Set-Cookie",
                            f"arena_session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800{secure}",
                        )
                    ],
                )
            if path == "/api/logout":
                u = self.user()
                cookie = self.headers.get("Cookie", "")
                token = next(
                    (
                        x.split("=", 1)[1]
                        for x in cookie.split("; ")
                        if x.startswith("arena_session=")
                    ),
                    None,
                )
                if u and token:
                    database.delete_session(hashlib.sha256(token.encode()).hexdigest())
                return self.send_json(
                    {"ok": True},
                    200,
                    [
                        (
                            "Set-Cookie",
                            "arena_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0",
                        )
                    ],
                )

            u = self.user()

            if path == "/api/enroll-single":
                u = self.need()
                if u["role"] != "student":
                    raise PermissionError("Only students can enroll in sports.")
                res = database.enroll_single(u["id"], data.get("game_id"))
                return self.send_json(res, 201)

            if path == "/api/withdraw":
                u = self.need()
                if u["role"] != "student":
                    raise PermissionError("Only students can withdraw from events.")
                res = database.withdraw_from_game(u["id"], data.get("game_id"))
                return self.send_json(res, 200)

            if path == "/api/waiting-list":
                u = self.need()
                if u["role"] != "student":
                    raise PermissionError("Only students can join waiting lists.")
                res = database.join_waiting_list(u["id"], data.get("game_id"))
                return self.send_json(res, 201)

            if path == "/api/factions":
                self.need("admin")
                fid = database.create_faction(data)
                return self.send_json({"id": fid, "created": True}, 201)

            if path == "/api/factions/assign":
                self.need("admin")
                database.assign_student_faction(data.get("user_id"), data.get("faction"))
                return self.send_json({"assigned": True}, 200)

            if path == "/api/matches":
                self.need("admin")
                venue = str(data.get("venue", "")).strip()
                if venue and venue not in ALLOWED_VENUES:
                    raise ValueError(f"Location must be one of: {', '.join(ALLOWED_VENUES)}.")
                mid = database.create_match(data)
                return self.send_json({"id": mid, "created": True}, 201)

            if path == "/api/announcements":
                u = self.need("admin")
                aid = database.create_announcement(data, u["id"])
                return self.send_json({"id": aid, "created": True}, 201)

            if path == "/api/participants":
                self.need("admin")
                name = str(data.get("name", "")).strip()
                username = str(data.get("username", "")).strip().lower()
                email = str(data.get("email", "")).strip().lower()
                faction = str(data.get("faction", "")).strip()
                password = str(data.get("password", ""))
                if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,39}", username):
                    raise ValueError(
                        "Use 3–40 letters, numbers, dots, underscores, or hyphens for the username."
                    )
                if len(email) > 254 or not re.fullmatch(
                    r"[^\s@]+@[^\s@]+\.[^\s@]+", email
                ):
                    raise ValueError("Enter a valid email address.")
                if not name or len(name) > 120 or not faction or len(faction) > 80:
                    raise ValueError(
                        "Name and faction are required and must fit the allowed length."
                    )
                valid_factions = {f["name"].strip().lower(): f["name"] for f in database.factions()}
                if not valid_factions:
                    raise ValueError("No active factions are configured by the administrator.")
                if faction.lower() not in valid_factions:
                    raise ValueError(f"Please select a valid faction managed by the administrator.")
                faction = valid_factions[faction.lower()]
                if not 8 <= len(password) <= 128:
                    raise ValueError(
                        "Use a starter password between 8 and 128 characters."
                    )
                participant_id = database.create_user(
                    {
                        "name": name,
                        "username": username,
                        "email": email,
                        "faction": faction,
                    },
                    password_hash(password),
                )
                return self.send_json({"id": participant_id, "created": True}, 201)

            if path == "/api/tournaments":
                self.need("admin")
                if not str(data.get("name", "")).strip():
                    raise ValueError("Tournament name is required.")
                return self.send_json({"id": database.create_tournament(data)}, 201)

            if path == "/api/games":
                self.need("admin")
                for k in ("name", "tournament_id", "starts_at", "venue", "capacity"):
                    if not data.get(k):
                        raise ValueError(f"{k.replace('_',' ').title()} is required.")
                venue = str(data.get("venue", "")).strip()
                if venue not in ALLOWED_VENUES:
                    raise ValueError(f"Location must be one of: {', '.join(ALLOWED_VENUES)}.")
                if int(data["capacity"]) < 1 or int(data.get("rounds", 1)) < 1:
                    raise ValueError("Capacity and rounds must be at least one.")
                return self.send_json({"id": database.create_game(data)}, 201)

            if path == "/api/choices":
                u = self.need()
                if u["role"] != "student":
                    raise PermissionError("Only students can submit game choices.")
                game_ids = data.get("game_ids")
                if not isinstance(game_ids, list) or len(game_ids) > 5:
                    raise ValueError("Choose up to five games.")
                database.enroll(u["id"], [int(x) for x in game_ids])
                return self.send_json({"submitted": True}, 201)

            if path == "/api/results":
                u = self.need("admin")
                database.record_results(
                    data.get("game_id"), data.get("round"), data.get("entries"), u["id"]
                )
                return self.send_json({"saved": True}, 200)

            # DS LAB - Phase 1 Endpoints
            if path == "/api/ds-lab/phase1/linked-list":
                action = data.get("action", "traverse")
                items = data.get("items", [])
                ll = LinkedList()
                for item in items:
                    ll.insert_at_end(item)

                res = {"action": action, "success": True}
                if action == "insert_start":
                    ll.insert_at_start(data.get("data"))
                    res["message"] = f"Inserted at beginning: {data.get('data')}"
                elif action == "insert_end":
                    ll.insert_at_end(data.get("data"))
                    res["message"] = f"Inserted at end: {data.get('data')}"
                elif action == "insert_pos":
                    pos = int(data.get("position", 0))
                    ll.insert_at_position(pos, data.get("data"))
                    res["message"] = f"Inserted at position {pos}: {data.get('data')}"
                elif action == "delete_id":
                    sid = str(data.get("student_id", ""))
                    del_item = ll.delete_by_student_id(sid)
                    res["deleted"] = del_item
                    res["message"] = f"Deleted student ID '{sid}': {del_item is not None}"
                elif action == "delete_val":
                    val = data.get("value")
                    del_item = ll.delete_by_value(val)
                    res["deleted"] = del_item
                    res["message"] = f"Deleted value '{val}': {del_item is not None}"
                elif action == "delete_pos":
                    pos = int(data.get("position", 0))
                    del_item = ll.delete_at_position(pos)
                    res["deleted"] = del_item
                    res["message"] = f"Deleted node at position {pos}: {del_item}"
                elif action == "search":
                    idx, found = ll.search(data.get("query"), data.get("field"))
                    res["index"] = idx
                    res["found"] = found
                    res["message"] = f"Searched for '{data.get('query')}': index {idx}"

                res["nodes"] = ll.traverse()
                res["length"] = len(ll)
                return self.send_json(res)

            if path == "/api/ds-lab/phase1/stack":
                action = data.get("action", "display")
                items = data.get("items", [])
                stk = Stack()
                for x in reversed(items):
                    stk.push(x)

                res = {"action": action}
                if action == "push":
                    val = data.get("value")
                    stk.push(val)
                    res["message"] = f"Pushed '{val}' onto stack."
                elif action == "pop":
                    popped = stk.pop()
                    res["popped"] = popped
                    res["message"] = f"Popped '{popped}' from stack." if popped is not None else "Stack Underflow: Stack is empty."
                elif action == "peek":
                    res["top"] = stk.peek()
                    res["message"] = f"Top element is '{stk.peek()}'." if stk.peek() is not None else "Stack is empty."

                res["stack"] = stk.display()
                res["size"] = len(stk)
                res["is_empty"] = stk.is_empty()
                return self.send_json(res)

            if path == "/api/ds-lab/phase1/queue":
                action = data.get("action", "display")
                items = data.get("items", [])
                q = Queue()
                for x in items:
                    q.enqueue(x)

                res = {"action": action}
                if action == "enqueue":
                    val = data.get("value")
                    q.enqueue(val)
                    res["message"] = f"Enqueued '{val}' to queue rear."
                elif action == "dequeue":
                    deq = q.dequeue()
                    res["dequeued"] = deq
                    res["message"] = f"Dequeued '{deq}' from queue front." if deq is not None else "Empty Queue: No elements to dequeue."
                elif action == "peek":
                    res["front"] = q.peek()
                    res["message"] = f"Front element is '{q.peek()}'." if q.peek() is not None else "Queue is empty."

                res["queue"] = q.display()
                res["size"] = len(q)
                res["is_empty"] = q.is_empty()
                return self.send_json(res)

            if path == "/api/ds-lab/phase1/expression":
                expr = str(data.get("expression", "100 + 25 * 4"))
                detailed = evaluate_expression_detailed(expr)
                return self.send_json(detailed)

            # DS LAB - Phase 2 Endpoints
            if path == "/api/ds-lab/phase2/bracket":
                tree = TournamentBinaryTree.build_sample_bracket()
                return self.send_json({
                    "bracket": tree.to_dict(),
                    "inorder": tree.inorder(),
                    "preorder": tree.preorder(),
                    "postorder": tree.postorder(),
                    "traversal_explanations": {
                        "inorder": "Left Subtree -> Root -> Right Subtree",
                        "preorder": "Root -> Left Subtree -> Right Subtree",
                        "postorder": "Left Subtree -> Right Subtree -> Root",
                    }
                })

            if path == "/api/ds-lab/phase2/bst":
                action = data.get("action", "build")
                values = data.get("values", [50, 30, 70, 20, 40, 60, 80])
                bst = BinarySearchTree()
                for v in values:
                    bst.insert(int(v))

                res = {"action": action}
                if action == "insert":
                    new_val = int(data.get("value"))
                    bst.insert(new_val)
                    res["message"] = f"Inserted {new_val} into BST."
                elif action == "delete":
                    del_val = int(data.get("value"))
                    ok = bst.delete(del_val)
                    res["message"] = f"Deleted {del_val} from BST." if ok else f"Value {del_val} not found in BST."
                    res["deleted"] = ok
                elif action == "search":
                    query_val = int(data.get("value"))
                    found = bst.contains(query_val)
                    res["found"] = found
                    res["message"] = f"Search for {query_val}: {'Found in BST' if found else 'Not Found'}"

                res["inorder"] = bst.inorder()
                res["preorder"] = bst.preorder()
                res["postorder"] = bst.postorder()
                res["min"] = bst.find_min()
                res["max"] = bst.find_max()
                res["tree"] = bst.to_dict()
                res["count"] = len(bst)
                return self.send_json(res)

            if path == "/api/ds-lab/phase2/graph":
                campus_venues = list(ALLOWED_VENUES)
                campus_edges = [
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
                g = Graph(campus_venues)
                for u_v, v_v in campus_edges:
                    g.add_edge(u_v, v_v)

                custom_edges = data.get("extra_edges", [])
                for u_v, v_v in custom_edges:
                    g.add_edge(u_v, v_v)

                start_venue = str(data.get("start", "Indoor Sports Complex"))
                if start_venue not in ALLOWED_VENUES:
                    start_venue = "Indoor Sports Complex"
                bfs_res = g.bfs_detailed(start_venue)
                dfs_res = g.dfs_detailed(start_venue)

                return self.send_json({
                    "venues": g.get_vertices(),
                    "connections": g.get_edges(),
                    "start": start_venue,
                    "bfs": bfs_res,
                    "dfs": dfs_res,
                })

            # DS LAB - Phase 3 Endpoints
            if path == "/api/ds-lab/phase3/search":
                items = data.get("items") or player_rows()
                query_str = str(data.get("query", ""))
                method = data.get("method", "linear")
                field = data.get("field", "name")

                if method == "binary":
                    res = binary_search_detailed(items, query_str, field)
                else:
                    res = linear_search_detailed(items, query_str, field)
                return self.send_json(res)

            if path == "/api/ds-lab/phase3/sort":
                items = data.get("items") or player_rows()
                field = data.get("field", "points")
                descending = bool(data.get("descending", True))
                res = merge_sort_detailed(items, field, descending)
                return self.send_json(res)

            # DS LAB - Phase 4 Endpoints
            if path == "/api/ds-lab/phase4/greedy-schedule":
                candidates = data.get("candidates", [])
                if not candidates:
                    candidates = [
                        {"id": 1, "name": "100m Sprint Heats", "venue": "Athletics Track", "start": 9.0, "end": 10.5, "participants": ["Aarav Nair", "Ishan Kapoor"], "capacity": 20, "priority": 3},
                        {"id": 2, "name": "Badminton Singles R1", "venue": "Badminton Court", "start": 9.5, "end": 11.0, "participants": ["Diya Menon", "Meera Rao"], "capacity": 10, "priority": 2},
                        {"id": 3, "name": "Basketball 3x3 Showcase", "venue": "Basketball Court", "start": 10.0, "end": 11.5, "participants": ["Rohan Shah", "Sana Khan"], "capacity": 12, "priority": 2},
                        {"id": 4, "name": "Relay 4x100m", "venue": "Athletics Track", "start": 10.0, "end": 11.5, "participants": ["Aarav Nair", "Vivaan Iyer"], "capacity": 30, "priority": 1},
                        {"id": 5, "name": "Cricket Tournament Match", "venue": "Cricket Ground", "start": 11.0, "end": 13.0, "participants": ["Zoya Pillai", "Ishan Kapoor"], "capacity": 22, "priority": 2},
                        {"id": 6, "name": "Volleyball Clash", "venue": "Volleyball Court", "start": 11.5, "end": 13.5, "participants": ["Vivaan Iyer", "Diya Menon"], "capacity": 25, "priority": 1},
                        {"id": 7, "name": "Tennis Championship Finals", "venue": "Tennis Court", "start": 11.0, "end": 12.5, "participants": ["Meera Rao"], "capacity": 8, "priority": 3},
                        {"id": 8, "name": "Multi-Sport Grand Final", "venue": "Indoor Sports Complex", "start": 14.0, "end": 16.0, "participants": ["Aarav Nair", "Rohan Shah"], "capacity": 50, "priority": 3},
                    ]
                result = schedule_tournament_events(candidates)
                return self.send_json(result)

            if path == "/api/ds-lab/phase4/commit-schedule":
                self.need("admin")
                approved = data.get("approved_events", [])
                tournament_id = int(data.get("tournament_id", 5))
                count = 0
                for ev in approved:
                    try:
                        starts_hour = float(ev.get("start", 9.0))
                        duration_mins = int((float(ev.get("end", starts_hour + 1.0)) - starts_hour) * 60)
                        start_time = datetime(2026, 10, 16, int(starts_hour), int((starts_hour % 1) * 60))
                        gid = database.create_game({
                            "tournament_id": tournament_id,
                            "name": ev["name"],
                            "venue": ev["venue"],
                            "starts_at": start_time,
                            "duration_minutes": duration_mins,
                            "capacity": int(ev.get("capacity", 20)),
                            "rounds": 1,
                            "category": "Scheduled Fixture"
                        })
                        database.create_match({
                            "game_id": gid,
                            "round_number": 1,
                            "match_name": ev["name"],
                            "venue": ev["venue"],
                            "starts_at": start_time,
                            "status": "upcoming",
                            "notes": f"Greedy schedule approved by administrator. Priority: {ev.get('priority', 1)}."
                        })
                        count += 1
                    except Exception as ex:
                        pass
                return self.send_json({"committed": True, "count": count})

            # Existing search/sort/greedy backward-compatible endpoints
            if path == "/api/expression":
                return self.send_json(
                    {
                        "result": evaluate_simple_expression(
                            str(data.get("expression", ""))
                        )
                    }
                )
            if path == "/api/greedy":
                return self.send_json(
                    {"selected": schedule_maximum_matches(data.get("matches", []))}
                )
            if path == "/api/search":
                items = player_rows()
                method = data.get("method", "linear")
                if method == "binary":
                    items = sorted(items, key=lambda x: x["name"].casefold())
                idx = (
                    linear_search(items, data.get("query", ""))
                    if method == "linear"
                    else binary_search(items, data.get("query", ""))
                )
                return self.send_json(
                    {"index": idx, "player": items[idx] if idx >= 0 else None}
                )
            if path == "/api/sort":
                items = player_rows()
                method = data.get("method", "merge")
                sorter = selection_sort if method == "selection" else merge_sort
                return self.send_json({"players": sorter(items, "points", True)})

            return self.send_json({"error": "Not found"}, 404)
        except Exception as e:
            return self.error(e)

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    print(f"Arena API listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
