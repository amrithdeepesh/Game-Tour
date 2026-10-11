"""Tournament API with role sessions and integrated operations algorithms."""
import hashlib,json,secrets,ipaddress,socket,os,re,time,threading
from datetime import datetime,timedelta,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
import mysql.connector,database
from algorithms.expression_handler import evaluate_simple_expression
from algorithms.problem_solver import schedule_maximum_matches
from algorithms.search_sort import binary_search,linear_search,merge_sort,selection_sort
from data_structures.tree import BinarySearchTree
from data_structures.linked_list import LinkedList
from data_structures.stack import Stack
from data_structures.queue import Queue
from data_structures.graph import Graph

def _allowed_frontend_origin(origin):
 if not origin:return False
 configured={x.strip().rstrip("/") for x in os.getenv("FRONTEND_ORIGINS","").split(",") if x.strip()}
 if origin.rstrip("/") in configured:return True
 try:
  parsed=urlparse(origin)
  if parsed.scheme!="http" or parsed.port!=3000 or not parsed.hostname:return False
  host=parsed.hostname.lower().rstrip(".")
  return host in ("localhost","127.0.0.1","::1",socket.gethostname().lower())
 except (ValueError,TypeError):return False

_LOGIN_FAILURES={}
_LOGIN_LOCK=threading.Lock()
def _login_blocked(key):
 now=time.monotonic()
 with _LOGIN_LOCK:
  attempts=[t for t in _LOGIN_FAILURES.get(key,[]) if now-t<900]
  _LOGIN_FAILURES[key]=attempts
  return len(attempts)>=5
def _login_failed(key):
 now=time.monotonic()
 with _LOGIN_LOCK:
  attempts=[t for t in _LOGIN_FAILURES.get(key,[]) if now-t<900]
  attempts.append(now);_LOGIN_FAILURES[key]=attempts
def _login_succeeded(key):
 with _LOGIN_LOCK:_LOGIN_FAILURES.pop(key,None)

def password_hash(password):
 salt=secrets.token_bytes(16);return salt.hex()+":"+hashlib.pbkdf2_hmac("sha256",password.encode(),salt,240000).hex()
def password_ok(password,saved):
 try:
  salt,key=saved.split(":");return secrets.compare_digest(hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),240000).hex(),key)
 except:return False
def player_rows():
 return [{"student_id":str(r["user_id"]),"name":r["display_name"],"faction":r["faction"],"points":r["points"],"wins":r["first_places"],"game":"All tournaments"} for r in database.leaderboard()]
def scheduled_rows(games):
 rows=[]
 for g in games:
  dt=g["starts_at"]
  if isinstance(dt,str):dt=datetime.fromisoformat(dt)
  start=(dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt).timestamp()
  rows.append({"name":g["name"],"start":start,"end":start+max(1,int(g.get("duration_minutes",60)))*60})
 return rows
def phase_demo():
 # The same data records used by registration and game choices are loaded into
 # the linked-list demo, so the visualization is backed by the real structure.
 linked = LinkedList()
 for entry in database.choices():
  linked.insert_at_end({
   "student_id": "ST" + str(entry["user_id"]),
   "name": entry["display_name"],
   "game": entry["game"],
  })

 players = player_rows()
 values = [player["points"] for player in players if player["points"] > 0] or [20, 40, 60, 80, 100]
 tree = BinarySearchTree()
 for value in values:
  tree.insert(value)

 action_stack = Stack()
 for action in ("Student registered", "Game choice submitted", "Score recorded"):
  action_stack.push(action)
 check_in_queue = Queue()
 for match in ("Next match check-in", "Following match check-in"):
  check_in_queue.enqueue(match)

 venues = Graph(("Arena", "Chess Hall", "Court A", "Table Tennis Hall"))
 for first, second in (
  ("Arena", "Chess Hall"),
  ("Arena", "Court A"),
  ("Arena", "Table Tennis Hall"),
  ("Chess Hall", "Court A"),
  ("Court A", "Table Tennis Hall"),
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
  "graph": {"bfs": venues.bfs("Arena"), "dfs": venues.dfs("Arena")},
  "greedySchedule": schedule_maximum_matches(intervals),
}

class Handler(BaseHTTPRequestHandler):
 def send_json(self,data,status=200,extra=None):
  body=json.dumps(data,default=str).encode();self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("X-Content-Type-Options","nosniff");self.send_header("Cache-Control","no-store")
  origin=self.headers.get("Origin")
  if _allowed_frontend_origin(origin):
   self.send_header("Access-Control-Allow-Origin",origin);self.send_header("Access-Control-Allow-Credentials","true");self.send_header("Vary","Origin")
  self.send_header("Access-Control-Allow-Headers","Content-Type");self.send_header("Access-Control-Allow-Methods","GET,POST,PUT,DELETE,OPTIONS")
  for k,v in extra or []:self.send_header(k,v)
  self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
 def payload(self):
  try:length=int(self.headers.get("Content-Length","0"))
  except (TypeError,ValueError):raise ValueError("Invalid request length.")
  if length<0 or length>1048576:raise ValueError("Request is too large.")
  if length and "application/json" not in self.headers.get("Content-Type","").lower():raise ValueError("Send the form as JSON.")
  try:data=json.loads(self.rfile.read(length) or b"{}")
  except (json.JSONDecodeError,UnicodeDecodeError):raise ValueError("Request data is not valid JSON.")
  if not isinstance(data,dict):raise ValueError("Request data must be an object.")
  return data
 def require_trusted_origin(self):
  origin=self.headers.get("Origin")
  if not origin or not _allowed_frontend_origin(origin):raise PermissionError("This website origin is not allowed.")
 def user(self):
  token=next((x.split("=",1)[1] for x in self.headers.get("Cookie","").split("; ") if x.startswith("arena_session=")),None)
  return database.session_user(hashlib.sha256(token.encode()).hexdigest()) if token else None
 def need(self,role=None):
  u=self.user()
  if not u:raise PermissionError("Please sign in to continue.")
  if role and u["role"]!=role:raise PermissionError("This action is available to administrators only.")
  return u
 def error(self,e):
  if isinstance(e,PermissionError):return self.send_json({"error":str(e)},401)
  if isinstance(e,ValueError):return self.send_json({"error":str(e)},400)
  if isinstance(e,mysql.connector.IntegrityError):return self.send_json({"error":"That account or record already exists, or its details are invalid."},409)
  if isinstance(e,(RuntimeError,mysql.connector.Error)):return self.send_json({"error":str(e) if isinstance(e,RuntimeError) else "MySQL is unavailable. Check backend/.env and the local MySQL service."},503)
  return self.send_json({"error":"Could not complete this request. Check the supplied details and database connection."},500)
 def do_OPTIONS(self):self.send_json({})
 def do_PUT(self):
  path=urlparse(self.path).path
  try:
   self.require_trusted_origin();data=self.payload();self.need("admin")
   if path.startswith("/api/participants/") and path.endswith("/status"):
    participant_id=int(path.split("/")[-2]);database.set_participant_active(participant_id,bool(data.get("active")));return self.send_json({"saved":True})
   if path.startswith("/api/tournaments/"):
    database.update_tournament(int(path.rsplit("/",1)[1]),data);return self.send_json({"saved":True})
   if path.startswith("/api/games/"):
    database.update_game(int(path.rsplit("/",1)[1]),data);return self.send_json({"saved":True})
   return self.send_json({"error":"Not found"},404)
  except Exception as e:return self.error(e)
 def do_DELETE(self):
  path=urlparse(self.path).path
  try:
   self.require_trusted_origin();self.need("admin")
   if path.startswith("/api/tournaments/"):
    database.delete_tournament(int(path.rsplit("/",1)[1]));return self.send_json({"deleted":True})
   if path.startswith("/api/games/"):
    database.delete_game(int(path.rsplit("/",1)[1]));return self.send_json({"deleted":True})
   if path.startswith("/api/participants/"):
    database.delete_participant(int(path.rsplit("/",1)[1]));return self.send_json({"deleted":True})
   return self.send_json({"error":"Not found"},404)
  except Exception as e:return self.error(e)
 def do_GET(self):
  path=urlparse(self.path).path
  try:
   if path=="/api/health":database.init();return self.send_json({"ok":True,"database":"mysql"})
   if path=="/api/me":return self.send_json({"user":self.user()})
   u=self.need()
   if path=="/api/dashboard":
    gs=database.games();mine=database.choices(u["id"]) if u["role"]=="student" else [];leaders=player_rows();all_choices=database.choices()
    return self.send_json({"user":u,"tournaments":database.tournaments(),"games":gs,"my_games":mine,"choices":all_choices if u["role"]=="admin" else [],"players":leaders,"matches":scheduled_rows(gs),"stats":{"tournaments":len(database.tournaments()),"games":len(gs),"students":len(database.query("SELECT id FROM users WHERE role='student' AND is_active=1")),"enrolled":len(all_choices)}})
   if path=="/api/games":return self.send_json({"games":database.games()})
   if path=="/api/tournaments":return self.send_json({"tournaments":database.tournaments()})
   if path=="/api/choices":return self.send_json({"choices":database.choices(None if u["role"]=="admin" else u["id"])})
   if path.startswith("/api/game-leaderboard/"):
    game_id=int(path.rsplit("/",1)[1])
    return self.send_json({"leaders":database.game_leaderboard(game_id)})
   params=parse_qs(urlparse(self.path).query)
   tournament_id=params.get("tournament_id",[None])[0]
   if path=="/api/leaderboard":return self.send_json({"leaders":database.leaderboard(tournament_id=int(tournament_id) if tournament_id else None)})
   if path=="/api/faction-leaderboard":return self.send_json({"leaders":database.leaderboard(True,int(tournament_id) if tournament_id else None)})
   if path=="/api/participants":self.need("admin");return self.send_json({"participants":database.participants()})
   if path=="/api/students":self.need("admin");return self.send_json({"students":database.students()})
   if path=="/api/results/audit":
    self.need("admin");game_id=int(params.get("game_id",["0"])[0]);return self.send_json({"audit":database.result_audit(game_id)})
   if path=="/api/results":
    self.need("admin");game_id=params.get("game_id",[None])[0];round_no=params.get("round",[None])[0]
    return self.send_json({"results":database.results(int(game_id) if game_id else None,int(round_no) if round_no else None)})
   if path=="/api/demo":return self.send_json(phase_demo())
   return self.send_json({"error":"Not found"},404)
  except Exception as e:return self.error(e)
 def do_POST(self):
  path=urlparse(self.path).path
  try:
   self.require_trusted_origin();data=self.payload()
   if path=="/api/register":
    username=str(data.get("username","")).strip().lower();email=str(data.get("email","")).strip().lower();name=str(data.get("name","")).strip();faction=str(data.get("faction","")).strip();pw=str(data.get("password",""))
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,39}",username):raise ValueError("Use 3–40 letters, numbers, dots, underscores, or hyphens for the username.")
    if len(email)>254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email):raise ValueError("Enter a valid email address.")
    if not name or len(name)>120 or not faction or len(faction)>80:raise ValueError("Name and faction are required and must fit the allowed length.")
    if not 12<=len(pw)<=128:raise ValueError("Use a password between 12 and 128 characters.")
    database.create_user({"username":username,"email":email,"name":name,"faction":faction},password_hash(pw));return self.send_json({"created":True},201)
   if path=="/api/login":
    username=str(data.get("username","")).strip().lower();password=str(data.get("password",""));key=(self.client_address[0],username)
    if _login_blocked(key):return self.send_json({"error":"Too many sign-in attempts. Try again in 15 minutes."},429)
    row=database.user_by_username(username)
    if not row or not password_ok(password,row["password_hash"]):
     _login_failed(key);return self.send_json({"error":"Username or password is incorrect."},401)
    _login_succeeded(key)
    token=secrets.token_urlsafe(32);database.save_session(hashlib.sha256(token.encode()).hexdigest(),row["id"],datetime.utcnow()+timedelta(days=7))
    secure="; Secure" if os.getenv("COOKIE_SECURE","").lower() in ("1","true","yes") else ""
    return self.send_json({"user":database.user_by_id(row["id"])},200,[("Set-Cookie",f"arena_session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800{secure}")])
   if path=="/api/logout":
    u=self.user();cookie=self.headers.get("Cookie","");token=next((x.split("=",1)[1] for x in cookie.split("; ") if x.startswith("arena_session=")),None)
    if u and token:database.delete_session(hashlib.sha256(token.encode()).hexdigest())
    return self.send_json({"ok":True},200,[("Set-Cookie","arena_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")])
   u=self.need()
   if path=="/api/participants":
    self.need("admin")
    name=str(data.get("name","")).strip();username=str(data.get("username","")).strip().lower();email=str(data.get("email","")).strip().lower();faction=str(data.get("faction","")).strip();password=str(data.get("password",""))
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,39}",username):raise ValueError("Use 3–40 letters, numbers, dots, underscores, or hyphens for the username.")
    if len(email)>254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email):raise ValueError("Enter a valid email address.")
    if not name or len(name)>120 or not faction or len(faction)>80:raise ValueError("Name and faction are required and must fit the allowed length.")
    if not 12<=len(password)<=128:raise ValueError("Use a starter password between 12 and 128 characters.")
    participant_id=database.create_user({"name":name,"username":username,"email":email,"faction":faction},password_hash(password))
    return self.send_json({"id":participant_id,"created":True},201)
   if path=="/api/tournaments":
    self.need("admin")
    if not str(data.get("name","")).strip():raise ValueError("Tournament name is required.")
    return self.send_json({"id":database.create_tournament(data)},201)
   if path=="/api/games":
    self.need("admin")
    for k in ("name","tournament_id","starts_at","venue","capacity"):
     if not data.get(k):raise ValueError(f"{k.replace('_',' ').title()} is required.")
    if int(data["capacity"])<1 or int(data.get("rounds",1))<1:raise ValueError("Capacity and rounds must be at least one.")
    return self.send_json({"id":database.create_game(data)},201)
   if path=="/api/choices":
    if u["role"]!="student":raise PermissionError("Only students can submit game choices.")
    game_ids=data.get("game_ids")
    if not isinstance(game_ids,list) or len(game_ids)>5:raise ValueError("Choose up to five games.")
    database.enroll(u["id"],[int(x) for x in game_ids]);return self.send_json({"submitted":True},201)
   if path=="/api/results":
    self.need("admin");database.record_results(data.get("game_id"),data.get("round"),data.get("entries"),u["id"]);return self.send_json({"saved":True},200)
   if path=="/api/expression":return self.send_json({"result":evaluate_simple_expression(str(data.get("expression","")))})
   if path=="/api/greedy":return self.send_json({"selected":schedule_maximum_matches(data.get("matches",[]))})
   if path=="/api/search":
    items=player_rows();method=data.get("method","linear")
    if method=="binary":items=sorted(items,key=lambda x:x["name"].casefold())
    idx=linear_search(items,data.get("query","")) if method=="linear" else binary_search(items,data.get("query",""))
    return self.send_json({"index":idx,"player":items[idx] if idx>=0 else None})
   if path=="/api/sort":
    items=player_rows();method=data.get("method","merge");sorter=selection_sort if method=="selection" else merge_sort
    return self.send_json({"players":sorter(items,"points",True)})
   return self.send_json({"error":"Not found"},404)
  except Exception as e:return self.error(e)
 def log_message(self,*_):pass
if __name__ == "__main__":
 host = os.getenv("API_HOST", "127.0.0.1")
 port = int(os.getenv("API_PORT", "8000"))
 print(f"Arena API listening on http://{host}:{port}")
 ThreadingHTTPServer((host, port), Handler).serve_forever()
