"""Tournament DS & Algorithms API. Uses only Python's standard library."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from algorithms.expression_handler import evaluate_simple_expression
from algorithms.problem_solver import schedule_maximum_matches
from algorithms.search_sort import linear_search, binary_search, selection_sort, merge_sort
from data_structures.linked_list import LinkedList
from data_structures.stack import Stack
from data_structures.queue import Queue
from data_structures.tree import BinarySearchTree

players = [
    {"student_id":"ST001","name":"Aarav Sharma","faction":"Red Dragons","game":"Chess","points":1240,"wins":8,"status":"Active"},
    {"student_id":"ST002","name":"Mira Patel","faction":"Blue Warriors","game":"Badminton","points":1185,"wins":7,"status":"Active"},
    {"student_id":"ST003","name":"Kabir Nair","faction":"Green Titans","game":"Table Tennis","points":1090,"wins":6,"status":"Active"},
    {"student_id":"ST004","name":"Ananya Rao","faction":"Gold Falcons","game":"Chess","points":1035,"wins":5,"status":"Active"},
    {"student_id":"ST005","name":"Ishaan Gupta","faction":"Red Dragons","game":"Badminton","points":980,"wins":5,"status":"Active"},
    {"student_id":"ST006","name":"Diya Menon","faction":"Blue Warriors","game":"Table Tennis","points":925,"wins":4,"status":"Active"},
]
matches = [{"name":"Chess · Round 3","start":9,"end":11},{"name":"Badminton · Semi-final","start":10,"end":12},{"name":"Table Tennis · Final","start":12,"end":14},{"name":"Chess · Final","start":13,"end":15}]
def leaderboard():
    return sorted(players, key=lambda p: (-p["points"], p["name"]))
def demo():
    ll = LinkedList()
    for p in players[:4]: ll.insert_at_end(p)
    stack = Stack()
    for action in ["Register ST007","Score updated ST002","Match completed ST001"]: stack.push(action)
    queue = Queue()
    for m in matches: queue.enqueue(m["name"])
    tree = BinarySearchTree()
    for score in [1240,1185,1090,1035,980,925]: tree.insert(score)
    graph = {"Arena": ["Chess Hall","Court A","Table Tennis Hall"], "Chess Hall": ["Arena","Court A"], "Court A": ["Arena","Chess Hall","Table Tennis Hall"], "Table Tennis Hall": ["Arena","Court A"]}
    def walk(start, depth=False):
        seen, order, pending = set(), [], [start]
        while pending:
            n = pending.pop() if depth else pending.pop(0)
            if n in seen: continue
            seen.add(n); order.append(n)
            pending.extend(x for x in graph[n] if x not in seen)
        return order
    return {"linkedList":ll.traverse(),"stackTop":stack.peek(),"stackActions":["Register ST007","Score updated ST002","Match completed ST001"],"queueFront":queue.peek(),"queueItems":[m["name"] for m in matches],"tree":{"inorder":tree.inorder(),"preorder":tree.preorder(),"postorder":tree.postorder()},"graph":{"bfs":walk("Arena"),"dfs":walk("Arena")},"greedySchedule":schedule_maximum_matches(matches)}
class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body=json.dumps(data).encode()
        self.send_response(status); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS"); self.end_headers(); self.wfile.write(body)
    def do_OPTIONS(self): self.send_json({})
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/health": return self.send_json({"ok":True,"service":"Tournament API"})
        if path in ("/api/dashboard","/api/players"): return self.send_json({"players":leaderboard(),"matches":matches,"demo":demo(),"stats":{"players":len(players),"matchesToday":12,"activeArenas":4,"completion":72}})
        if path=="/api/demo": return self.send_json(demo())
        self.send_json({"error":"Not found"},404)
    def do_POST(self):
        try:
            payload=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))) or b"{}")
            path=urlparse(self.path).path
            if path=="/api/players":
                name=str(payload.get("name","")).strip()
                if not name: return self.send_json({"error":"Player name is required"},400)
                item={"student_id":"ST%03d"%(len(players)+1),"name":name,"faction":payload.get("faction","Red Dragons"),"game":payload.get("game","Chess"),"points":0,"wins":0,"status":"Active"}
                players.append(item); return self.send_json(item,201)
            if path=="/api/expression": return self.send_json({"result":evaluate_simple_expression(str(payload.get("expression","")))})
            if path=="/api/greedy": return self.send_json({"selected":schedule_maximum_matches(payload.get("matches",matches))})
            if path=="/api/search":
                method=payload.get("method","linear")
                items=players if method=="linear" else sorted(players,key=lambda p:p["name"].casefold())
                index=linear_search(items,payload.get("query","")) if method=="linear" else binary_search(items,payload.get("query",""))
                return self.send_json({"method":method,"index":index,"player":items[index] if index>=0 else None})
            if path=="/api/sort":
                method=payload.get("method","merge")
                sorter=selection_sort if method=="selection" else merge_sort
                return self.send_json({"method":method,"players":sorter(players,"points",True)})
            self.send_json({"error":"Not found"},404)
        except (ValueError,ZeroDivisionError) as exc: self.send_json({"error":str(exc)},400)
    def log_message(self, *_): pass
if __name__=="__main__":
    print("Tournament API ready at http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1",8000),Handler).serve_forever()
