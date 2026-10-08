"""Tournament Data Structures & Algorithms API backed by MySQL."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import mysql.connector

import database
from algorithms.expression_handler import evaluate_simple_expression
from algorithms.problem_solver import schedule_maximum_matches
from algorithms.search_sort import binary_search, linear_search, merge_sort, selection_sort
from data_structures.linked_list import LinkedList
from data_structures.queue import Queue
from data_structures.stack import Stack
from data_structures.tree import BinarySearchTree


def leaderboard(game=None):
    return database.list_leaderboard(game)


def demo(bundle=None):
    bundle = bundle or database.load_bundle()
    players = bundle["players"]
    matches = bundle["matches"]
    ll = LinkedList()
    for player in players[:4]:
        ll.insert_at_end(player)
    stack = Stack()
    for action in ["Register participant", "Score updated", "Match completed"]:
        stack.push(action)
    queue = Queue()
    for item in matches:
        queue.enqueue(item["name"])
    tree = BinarySearchTree()
    for score in sorted([p["points"] for p in players], reverse=True):
        tree.insert(score)
    graph = {
        "Arena": ["Chess Hall", "Court A", "Table Tennis Hall"],
        "Chess Hall": ["Arena", "Court A"],
        "Court A": ["Arena", "Chess Hall", "Table Tennis Hall"],
        "Table Tennis Hall": ["Arena", "Court A"],
    }

    def walk(start, depth=False):
        seen, order, pending = set(), [], [start]
        while pending:
            node = pending.pop() if depth else pending.pop(0)
            if node in seen:
                continue
            seen.add(node)
            order.append(node)
            neighbors = [neighbor for neighbor in graph[node] if neighbor not in seen]
            pending.extend(reversed(neighbors) if depth else neighbors)
        return order

    return {
        "linkedList": ll.traverse(),
        "stackTop": stack.peek(),
        "stackActions": ["Register participant", "Score updated", "Match completed"],
        "queueFront": queue.peek(),
        "queueItems": [item["name"] for item in matches],
        "tree": {
            "inorder": tree.inorder(),
            "preorder": tree.preorder(),
            "postorder": tree.postorder(),
        },
        "graph": {"bfs": walk("Arena"), "dfs": walk("Arena", True)},
        "greedySchedule": schedule_maximum_matches(matches),
    }


def dashboard():
    bundle = database.load_bundle()
    players = bundle["players"]
    active = [p for p in players if p["status"] == "Active"]
    pending = sum(p["status"] == "Pending" for p in players)
    result_count = len(bundle["results"])
    return {
        **bundle,
        "demo": demo(bundle),
        "stats": {
            "players": len(active),
            "pending": pending,
            "results": result_count,
            "matchesToday": len(bundle["matches"]),
            "activeArenas": len({item["arena"] for item in bundle["matches"]}),
            "completion": min(100, round(result_count / max(1, len(bundle["matches"])) * 100)),
        },
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,PATCH,OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")

    def handle_error(self, error):
        if isinstance(error, ValueError):
            return self.send_json({"error": str(error)}, 400)
        if isinstance(error, LookupError):
            return self.send_json({"error": str(error)}, 404)
        if isinstance(error, mysql.connector.IntegrityError):
            return self.send_json(
                {"error": "This record is linked to tournament history and cannot be removed."},
                409,
            )
        if isinstance(error, RuntimeError):
            return self.send_json({"error": str(error)}, 503)
        return self.send_json(
            {"error": "MySQL is unavailable. Check the local database settings and try again."},
            503,
        )

    def do_OPTIONS(self):
        self.send_json({})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        try:
            if path == "/api/health":
                database.initialize_database()
                return self.send_json({"ok": True, "database": "mysql"})
            if path in ("/api/dashboard", "/api/players"):
                return self.send_json(dashboard())
            if path == "/api/demo":
                return self.send_json(demo())
            if path == "/api/games":
                return self.send_json({"games": database.load_bundle()["games"]})
            if path == "/api/results":
                return self.send_json({"results": database.load_bundle()["results"]})
            if path == "/api/leaderboard":
                game = query.get("game", [None])[0]
                return self.send_json({"game": game, "players": leaderboard(game)})
            return self.send_json({"error": "Not found"}, 404)
        except Exception as error:
            return self.handle_error(error)

    def do_POST(self):
        try:
            payload = self.read_json()
            path = urlparse(self.path).path
            if path == "/api/players":
                return self.send_json(database.create_participant(payload), 201)
            if path == "/api/games":
                return self.send_json(database.create_game(payload), 201)
            if path == "/api/results":
                return self.send_json(database.record_result(payload), 201)
            if path == "/api/expression":
                return self.send_json({
                    "result": evaluate_simple_expression(str(payload.get("expression", "")))
                })
            if path == "/api/greedy":
                bundle = database.load_bundle()
                return self.send_json({
                    "selected": schedule_maximum_matches(payload.get("matches", bundle["matches"]))
                })
            if path == "/api/search":
                players = database.load_bundle()["players"]
                method = payload.get("method", "linear")
                items = players if method == "linear" else sorted(players, key=lambda p: p["name"].casefold())
                index = (
                    linear_search(items, payload.get("query", ""))
                    if method == "linear"
                    else binary_search(items, payload.get("query", ""))
                )
                return self.send_json({
                    "method": method,
                    "index": index,
                    "player": items[index] if index >= 0 else None,
                })
            if path == "/api/sort":
                players = database.load_bundle()["players"]
                method = payload.get("method", "merge")
                sorter = selection_sort if method == "selection" else merge_sort
                return self.send_json({"method": method, "players": sorter(players, "points", True)})
            return self.send_json({"error": "Not found"}, 404)
        except Exception as error:
            return self.handle_error(error)

    def do_PATCH(self):
        parts = urlparse(self.path).path.rstrip("/").split("/")
        if len(parts) != 5 or parts[1:3] != ["api", "players"] or parts[4] != "status":
            return self.send_json({"error": "Not found"}, 404)
        try:
            payload = self.read_json()
            player = database.set_participant_status(parts[3], payload.get("status"))
            return self.send_json(player)
        except Exception as error:
            return self.handle_error(error)

    def do_DELETE(self):
        parts = urlparse(self.path).path.rstrip("/").split("/")
        if len(parts) != 4 or parts[1:3] != ["api", "players"]:
            return self.send_json({"error": "Not found"}, 404)
        try:
            database.delete_participant(parts[3])
            return self.send_json({"deleted": parts[3]})
        except Exception as error:
            return self.handle_error(error)

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print("Tournament API on http://localhost:8000; MySQL initializes on the first API request.")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
