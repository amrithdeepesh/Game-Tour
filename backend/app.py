"""Tournament API with role sessions and the four interactive DS/algorithm phases."""
import hashlib,json,secrets,ipaddress,socket
from datetime import datetime,timedelta
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
import mysql.connector,database
from algorithms.expression_handler import evaluate_simple_expression
from algorithms.problem_solver import schedule_maximum_matches
from algorithms.search_sort import binary_search,linear_search,merge_sort,selection_sort
from data_structures.tree import BinarySearchTree

def _allowed_frontend_origin(origin):
 try:
  parsed=urlparse(origin or "")
  if parsed.scheme!="http" or parsed.port!=3000 or not parsed.hostname:return False
  host=parsed.hostname.lower().rstrip(".")
  if host in ("localhost","127.0.0.1","::1",socket.gethostname().lower()):return True
  address=ipaddress.ip_address(host)
  return address.is_loopback or address.is_private
 except (ValueError,TypeError):return False

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
  start=dt.timestamp()
  rows.append({"name":g["name"],"start":start,"end":start+max(1,int(g["rounds"]))*3600})
 return rows
def phase_demo():
 entries=database.choices()
 linked=[{"student_id":"ST"+str(x["user_id"]),"name":x["display_name"],"game":x["game"]} for x in entries]
 players=player_rows();values=[p["points"] for p in players if p["points"]>0] or [20,40,60,80,100]
 tree=BinarySearchTree()
 for value in values:tree.insert(value)
 graph={"Arena":["Chess Hall","Court A","Table Tennis Hall"],"Chess Hall":["Arena","Court A"],"Court A":["Arena","Chess Hall","Table Tennis Hall"],"Table Tennis Hall":["Arena","Court A"]}
 def walk(start,depth=False):
  seen=set();order=[];pending=[start]
  while pending:
   node=pending.pop() if depth else pending.pop(0)
   if node in seen:continue
   seen.add(node);order.append(node);neighbors=[n for n in graph[node] if n not in seen];pending.extend(reversed(neighbors) if depth else neighbors)
  return order
 intervals=scheduled_rows(database.games())
 return {"linkedList":linked,"stackTop":"Match completed","stackActions":["Student registered","Game choice submitted","Score recorded"],"queueFront":"Next match check-in","queueItems":["Next match check-in","Following match check-in"],"tree":{"inorder":tree.inorder(),"preorder":tree.preorder(),"postorder":tree.postorder()},"graph":{"bfs":walk("Arena"),"dfs":walk("Arena",True)},"greedySchedule":schedule_maximum_matches(intervals)}

class Handler(BaseHTTPRequestHandler):
 def send_json(self,data,status=200,extra=None):
  body=json.dumps(data,default=str).encode();self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");origin=self.headers.get("Origin")
  if _allowed_frontend_origin(origin):self.send_header("Access-Control-Allow-Origin",origin);self.send_header("Access-Control-Allow-Credentials","true");self.send_header("Vary","Origin")
  self.send_header("Access-Control-Allow-Headers","Content-Type");self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
  for k,v in extra or []:self.send_header(k,v)
  self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
 def payload(self):return json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))) or b"{}")
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
 def do_GET(self):
  path=urlparse(self.path).path
  try:
   if path=="/api/health":database.init();return self.send_json({"ok":True,"database":"mysql"})
   if path=="/api/me":return self.send_json({"user":self.user()})
   u=self.need()
   if path=="/api/dashboard":
    gs=database.games();mine=database.choices(u["id"]) if u["role"]=="student" else [];leaders=player_rows();all_choices=database.choices()
    return self.send_json({"user":u,"tournaments":database.tournaments(),"games":gs,"my_games":mine,"choices":all_choices if u["role"]=="admin" else [],"players":leaders,"matches":scheduled_rows(gs),"stats":{"tournaments":len(database.tournaments()),"games":len(gs),"students":len(database.query("SELECT id FROM users WHERE role='student'")),"enrolled":len(all_choices)}})
   if path=="/api/games":return self.send_json({"games":database.games()})
   if path=="/api/tournaments":return self.send_json({"tournaments":database.tournaments()})
   if path=="/api/choices":return self.send_json({"choices":database.choices(None if u["role"]=="admin" else u["id"])})
   if path=="/api/leaderboard":return self.send_json({"leaders":database.leaderboard()})
   if path=="/api/faction-leaderboard":return self.send_json({"leaders":database.leaderboard(True)})
   if path=="/api/participants":self.need("admin");return self.send_json({"participants":database.participants()})
   if path=="/api/results":self.need("admin");return self.send_json({"results":database.results()})
   if path=="/api/demo":return self.send_json(phase_demo())
   return self.send_json({"error":"Not found"},404)
  except Exception as e:return self.error(e)
 def do_POST(self):
  path=urlparse(self.path).path
  try:
   data=self.payload()
   if path=="/api/register":
    username=str(data.get("username","")).strip().lower();email=str(data.get("email","")).strip().lower();name=str(data.get("name","")).strip();faction=str(data.get("faction","")).strip();pw=str(data.get("password",""))
    if len(username)<3 or not email or not name or not faction or len(pw)<8:raise ValueError("Enter your details, a username of 3+ characters, and password of at least 8 characters.")
    database.create_user({"username":username,"email":email,"name":name,"faction":faction},password_hash(pw));return self.send_json({"created":True},201)
   if path=="/api/login":
    row=database.user_by_username(str(data.get("username","")).strip().lower())
    if not row or not password_ok(str(data.get("password","")),row["password_hash"]):return self.send_json({"error":"Username or password is incorrect."},401)
    token=secrets.token_urlsafe(32);database.save_session(hashlib.sha256(token.encode()).hexdigest(),row["id"],datetime.utcnow()+timedelta(days=7))
    return self.send_json({"user":database.user_by_id(row["id"])},200,[("Set-Cookie",f"arena_session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800")])
   if path=="/api/logout":
    u=self.user();cookie=self.headers.get("Cookie","");token=next((x.split("=",1)[1] for x in cookie.split("; ") if x.startswith("arena_session=")),None)
    if u and token:database.delete_session(hashlib.sha256(token.encode()).hexdigest())
    return self.send_json({"ok":True},200,[("Set-Cookie","arena_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")])
   u=self.need()
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
    database.enroll(u["id"],[int(x) for x in data.get("game_ids",[])]);return self.send_json({"submitted":True},201)
   if path=="/api/results":
    self.need("admin");database.record_match(data);return self.send_json({"saved":True},201)
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
if __name__=="__main__":print("Arena API listening on http://localhost:8000");ThreadingHTTPServer(("127.0.0.1",8000),Handler).serve_forever()
