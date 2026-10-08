"""Tournament DS & Algorithms API. Uses only Python's standard library."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from algorithms.expression_handler import evaluate_simple_expression
from algorithms.problem_solver import schedule_maximum_matches
from algorithms.search_sort import linear_search, binary_search, selection_sort, merge_sort
from data_structures.linked_list import LinkedList
from data_structures.stack import Stack
from data_structures.queue import Queue
from data_structures.tree import BinarySearchTree

games = [
    {"game_id":"G001","name":"Chess","category":"Strategy","venue":"Arena Chess Hall","description":"Individual strategy tournament","status":"Open"},
    {"game_id":"G002","name":"Badminton","category":"Racquet","venue":"Court A","description":"Singles and doubles brackets","status":"Open"},
    {"game_id":"G003","name":"Table Tennis","category":"Racquet","venue":"Table Tennis Hall","description":"Singles tournament","status":"Open"},
]
players = [
    {"student_id":"ST001","name":"Aarav Sharma","faction":"Red Dragons","game":"Chess","email":"aarav@example.edu","notes":"","points":1240,"wins":8,"status":"Active"},
    {"student_id":"ST002","name":"Mira Patel","faction":"Blue Warriors","game":"Badminton","email":"mira@example.edu","notes":"","points":1185,"wins":7,"status":"Active"},
    {"student_id":"ST003","name":"Kabir Nair","faction":"Green Titans","game":"Table Tennis","email":"kabir@example.edu","notes":"","points":1090,"wins":6,"status":"Active"},
    {"student_id":"ST004","name":"Ananya Rao","faction":"Gold Falcons","game":"Chess","email":"ananya@example.edu","notes":"","points":1035,"wins":5,"status":"Active"},
    {"student_id":"ST005","name":"Ishaan Gupta","faction":"Red Dragons","game":"Badminton","email":"ishaan@example.edu","notes":"","points":980,"wins":5,"status":"Active"},
    {"student_id":"ST006","name":"Diya Menon","faction":"Blue Warriors","game":"Table Tennis","email":"diya@example.edu","notes":"","points":925,"wins":4,"status":"Active"},
]
matches = [
    {"name":"Chess · Round 3","game":"Chess","arena":"Arena Chess Hall","start":9,"end":11},
    {"name":"Badminton · Semi-final","game":"Badminton","arena":"Court A","start":10,"end":12},
    {"name":"Table Tennis · Final","game":"Table Tennis","arena":"Table Tennis Hall","start":12,"end":14},
    {"name":"Chess · Final","game":"Chess","arena":"Arena Chess Hall","start":13,"end":15},
]
results = []

def leaderboard(game=None):
    active=[p for p in players if p.get("status")=="Active" and (not game or p["game"]==game)]
    return sorted(active,key=lambda p:(-p["points"],-p["wins"],p["name"].casefold()))

def dashboard():
    return {"players":leaderboard(),"matches":matches,"games":games,"results":results,"demo":demo(),
            "stats":{"players":len(players),"pending":sum(p["status"]=="Pending" for p in players),"results":len(results),"matchesToday":len(matches),"activeArenas":len({m["arena"] for m in matches}),
                     "completion":min(100,round(len(results)/max(1,len(matches))*100))}}

def demo():
    ll=LinkedList()
    for player in players[:4]: ll.insert_at_end(player)
    stack=Stack()
    for action in ["Register ST007","Score updated ST002","Match completed ST001"]: stack.push(action)
    queue=Queue()
    for match in matches: queue.enqueue(match["name"])
    tree=BinarySearchTree()
    for score in sorted([p["points"] for p in players],reverse=True): tree.insert(score)
    graph={"Arena":["Chess Hall","Court A","Table Tennis Hall"],"Chess Hall":["Arena","Court A"],
           "Court A":["Arena","Chess Hall","Table Tennis Hall"],"Table Tennis Hall":["Arena","Court A"]}
    def walk(start,depth=False):
        seen,order,pending=set(),[],[start]
        while pending:
            node=pending.pop() if depth else pending.pop(0)
            if node in seen: continue
            seen.add(node); order.append(node)
            neighbors=[x for x in graph[node] if x not in seen]
            pending.extend(reversed(neighbors) if depth else neighbors)
        return order
    return {"linkedList":ll.traverse(),"stackTop":stack.peek(),
            "stackActions":["Register ST007","Score updated ST002","Match completed ST001"],
            "queueFront":queue.peek(),"queueItems":[m["name"] for m in matches],
            "tree":{"inorder":tree.inorder(),"preorder":tree.preorder(),"postorder":tree.postorder()},
            "graph":{"bfs":walk("Arena"),"dfs":walk("Arena",True)},
            "greedySchedule":schedule_maximum_matches(matches)}

class Handler(BaseHTTPRequestHandler):
    def send_json(self,data,status=200):
        body=json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Access-Control-Allow-Methods","GET,POST,DELETE,PATCH,OPTIONS")
        self.end_headers(); self.wfile.write(body)
    def read_json(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))) or b"{}")
    def do_OPTIONS(self): self.send_json({})
    def do_GET(self):
        parsed=urlparse(self.path); path=parsed.path; query=parse_qs(parsed.query)
        if path=="/api/health": return self.send_json({"ok":True,"service":"Tournament API"})
        if path in ("/api/dashboard","/api/players"): return self.send_json(dashboard())
        if path=="/api/demo": return self.send_json(demo())
        if path=="/api/games": return self.send_json({"games":games})
        if path=="/api/results": return self.send_json({"results":results})
        if path=="/api/leaderboard":
            game=query.get("game",[None])[0]
            return self.send_json({"game":game,"players":leaderboard(game)})
        self.send_json({"error":"Not found"},404)
    def do_POST(self):
        try:
            payload=self.read_json(); path=urlparse(self.path).path
            if path=="/api/players":
                name=str(payload.get("name","")).strip()
                if not name: return self.send_json({"error":"Student name is required."},400)
                game=str(payload.get("game","")).strip()
                if game not in [g["name"] for g in games]: return self.send_json({"error":"Choose an available game."},400)
                item={"student_id":"ST%03d"%(max([int(p["student_id"][2:]) for p in players]+[0])+1),
                      "name":name,"faction":str(payload.get("faction","Open Entry")),
                      "game":game,"email":str(payload.get("email","")).strip(),
                      "notes":str(payload.get("notes","")).strip(),"points":0,"wins":0,"status":"Pending"}
                players.append(item); return self.send_json(item,201)
            if path=="/api/games":
                name=str(payload.get("name","")).strip()
                if not name: return self.send_json({"error":"Game name is required."},400)
                if any(g["name"].casefold()==name.casefold() for g in games): return self.send_json({"error":"That game already exists."},409)
                item={"game_id":"G%03d"%(len(games)+1),"name":name,
                      "category":str(payload.get("category","Other")).strip() or "Other",
                      "venue":str(payload.get("venue","Main Arena")).strip() or "Main Arena",
                      "description":str(payload.get("description","")).strip(),"status":"Open"}
                games.append(item); return self.send_json(item,201)
            if path=="/api/results":
                game=str(payload.get("game","")).strip()
                winner_id=str(payload.get("winner_id","")).strip()
                loser_id=str(payload.get("loser_id","")).strip()
                winner=next((p for p in players if p["student_id"]==winner_id),None)
                loser=next((p for p in players if p["student_id"]==loser_id),None)
                if game not in [g["name"] for g in games]: return self.send_json({"error":"Choose a valid game."},400)
                if not winner or not loser or winner is loser: return self.send_json({"error":"Choose two different registered participants."},400)
                if winner["game"]!=game or loser["game"]!=game: return self.send_json({"error":"Both participants must be registered in this game."},400)
                try:
                    win_score=int(payload.get("winner_score",0)); lose_score=int(payload.get("loser_score",0))
                    if min(win_score,lose_score)<0: raise ValueError
                except (ValueError,TypeError): return self.send_json({"error":"Scores must be zero or greater."},400)
                winner["points"]+=win_score; winner["wins"]+=1; loser["points"]+=lose_score
                entry={"result_id":"R%03d"%(len(results)+1),"game":game,
                       "match":str(payload.get("match","Final")).strip() or "Match",
                       "winner_id":winner_id,"winner":winner["name"],"winner_score":win_score,
                       "loser_id":loser_id,"loser":loser["name"],"loser_score":lose_score,
                       "played_at":str(payload.get("played_at","")).strip()}
                results.insert(0,entry); return self.send_json(entry,201)
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
    def do_PATCH(self):
        parts=urlparse(self.path).path.rstrip("/").split("/")
        if len(parts)==5 and parts[1:3]==["api","players"] and parts[4]=="status":
            student_id=parts[3]
            player=next((p for p in players if p["student_id"]==student_id),None)
            if not player: return self.send_json({"error":"Participant not found."},404)
            try: payload=self.read_json()
            except ValueError: return self.send_json({"error":"Invalid JSON."},400)
            status=payload.get("status")
            if status not in ("Active","Declined"): return self.send_json({"error":"Status must be Active or Declined."},400)
            player["status"]=status; return self.send_json(player)
        self.send_json({"error":"Not found"},404)
    def do_DELETE(self):
        parts=urlparse(self.path).path.rstrip("/").split("/")
        if len(parts)==4 and parts[1:3]==["api","players"]:
            for index,player in enumerate(players):
                if player["student_id"]==parts[3]:
                    return self.send_json({"deleted":players.pop(index)})
            return self.send_json({"error":"Participant not found"},404)
        self.send_json({"error":"Not found"},404)
    def log_message(self,*_): pass

if __name__=="__main__":
    print("Tournament API ready at http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1",8000),Handler).serve_forever()
