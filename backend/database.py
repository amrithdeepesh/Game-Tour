"""MySQL persistence layer; creates empty app tables and optional configured admin only."""
import os,threading,secrets,hashlib,json,re
from pathlib import Path
from datetime import datetime,timedelta,timezone
import mysql.connector
from mysql.connector import errorcode
_ready=False
_lock=threading.Lock()
def _env():
 p=Path(__file__).with_name(".env")
 if p.exists():
  for line in p.read_text(encoding="utf8").splitlines():
   line=line.strip()
   if line and not line.startswith("#") and "=" in line:
    k,v=line.split("=",1);os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
def connect(with_db=True):
 _env()
 if any(not os.getenv(k) for k in ("DB_USER","DB_PASSWORD","DB_NAME")):raise RuntimeError("MySQL setup required: set DB_USER, DB_PASSWORD, and DB_NAME in backend/.env.")
 cfg=dict(host=os.getenv("DB_HOST","127.0.0.1"),port=int(os.getenv("DB_PORT","3306")),user=os.environ["DB_USER"],password=os.environ["DB_PASSWORD"],connection_timeout=5,autocommit=False)
 if with_db:cfg["database"]=os.environ["DB_NAME"]
 return mysql.connector.connect(**cfg)
def init():
 global _ready
 if _ready:return
 with _lock:
  if _ready:return
  try:
   c=connect()
  except mysql.connector.Error as exc:
   if exc.errno != errorcode.ER_BAD_DB_ERROR:
    raise
   bootstrap=connect(False);cur=bootstrap.cursor()
   try:
    db=os.environ["DB_NAME"].replace("`","")
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    bootstrap.commit()
   finally:
    cur.close();bootstrap.close()
   c=connect()
  schema=[
  """CREATE TABLE IF NOT EXISTS users(id BIGINT AUTO_INCREMENT PRIMARY KEY,username VARCHAR(40) NOT NULL UNIQUE,email VARCHAR(254) NOT NULL UNIQUE,display_name VARCHAR(120) NOT NULL,faction VARCHAR(80) NOT NULL,password_hash VARCHAR(256) NOT NULL,role ENUM('admin','student') NOT NULL DEFAULT 'student',is_active TINYINT(1) NOT NULL DEFAULT 1,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS tournaments(id BIGINT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(120) NOT NULL,description VARCHAR(500) NOT NULL DEFAULT '',starts_at DATETIME NULL,ends_at DATETIME NULL,registration_closes_at DATETIME NULL,points_first INT NOT NULL DEFAULT 10,points_second INT NOT NULL DEFAULT 7,points_third INT NOT NULL DEFAULT 5,points_participation INT NOT NULL DEFAULT 1,status ENUM('upcoming','active','completed') NOT NULL DEFAULT 'upcoming',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS games(id BIGINT AUTO_INCREMENT PRIMARY KEY,tournament_id BIGINT NOT NULL,name VARCHAR(100) NOT NULL,category VARCHAR(80) NOT NULL DEFAULT '',rounds INT NOT NULL DEFAULT 1,starts_at DATETIME NOT NULL,duration_minutes INT NOT NULL DEFAULT 60,venue VARCHAR(160) NOT NULL,capacity INT NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,INDEX(tournament_id,starts_at),CONSTRAINT fk_game_tournament FOREIGN KEY(tournament_id) REFERENCES tournaments(id)) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS game_choices(user_id BIGINT NOT NULL,game_id BIGINT NOT NULL,chosen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(user_id,game_id),INDEX(game_id),CONSTRAINT fk_choice_user FOREIGN KEY(user_id) REFERENCES users(id),CONSTRAINT fk_choice_game FOREIGN KEY(game_id) REFERENCES games(id)) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS results(id BIGINT AUTO_INCREMENT PRIMARY KEY,game_id BIGINT NOT NULL,round_number INT NOT NULL,participant_id BIGINT NOT NULL,score INT NOT NULL DEFAULT 0,points_awarded INT NOT NULL DEFAULT 0,result_status ENUM('played','no_show','disqualified') NOT NULL DEFAULT 'played',placement INT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,UNIQUE KEY uq_result_game_round_participant(game_id,round_number,participant_id),INDEX(game_id,placement),CONSTRAINT fk_result_game FOREIGN KEY(game_id) REFERENCES games(id),CONSTRAINT fk_result_user FOREIGN KEY(participant_id) REFERENCES users(id)) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS sessions(token_hash CHAR(64) PRIMARY KEY,user_id BIGINT NOT NULL,expires_at DATETIME NOT NULL,CONSTRAINT fk_session_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS result_audit(id BIGINT AUTO_INCREMENT PRIMARY KEY,game_id BIGINT NOT NULL,round_number INT NOT NULL,participant_id BIGINT NOT NULL,actor_user_id BIGINT NULL,action VARCHAR(20) NOT NULL,before_values JSON NULL,after_values JSON NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,INDEX(game_id,created_at)) ENGINE=InnoDB"""]
  try:
   cur=c.cursor()
   for sql in schema:cur.execute(sql)
   migrations={
    "users":{"is_active":"TINYINT(1) NOT NULL DEFAULT 1"},
    "tournaments":{"registration_closes_at":"DATETIME NULL","points_first":"INT NOT NULL DEFAULT 10","points_second":"INT NOT NULL DEFAULT 7","points_third":"INT NOT NULL DEFAULT 5","points_participation":"INT NOT NULL DEFAULT 1"},
    "games":{"duration_minutes":"INT NOT NULL DEFAULT 60"},
    "results":{"points_awarded":"INT NOT NULL DEFAULT 0","result_status":"ENUM('played','no_show','disqualified') NOT NULL DEFAULT 'played'"},
   }
   for table,columns in migrations.items():
    for column,definition in columns.items():
     cur.execute("SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=%s AND column_name=%s",(table,column))
     if not cur.fetchone():
      cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}")
      if table=="results" and column=="points_awarded":
       cur.execute("UPDATE results SET points_awarded=score")
   cur.execute("SELECT 1 FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name='results' AND index_name='uq_result_game_round_participant'")
   if not cur.fetchone():
    cur.execute("ALTER TABLE results ADD UNIQUE KEY uq_result_game_round_participant(game_id,round_number,participant_id)")
   c.commit();cur.close()
  finally:c.close()
  # Provision exactly one admin only when private credentials were explicitly configured.
  username=os.getenv("ADMIN_USERNAME","").strip().lower();password=os.getenv("ADMIN_PASSWORD","")
  if username or password:
   if len(username)<3 or len(password)<12:raise RuntimeError("Set both ADMIN_USERNAME and a strong ADMIN_PASSWORD (at least 12 characters) in backend/.env.")
   salt=secrets.token_bytes(16);digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,240000).hex();pw_hash=salt.hex()+":"+digest
   c=connect();cur=c.cursor(dictionary=True)
   try:
    cur.execute("SELECT id,role FROM users WHERE username=%s",(username,));existing=cur.fetchone()
    if existing and existing["role"]!="admin":raise RuntimeError("Configured admin username already belongs to a student; choose a different ADMIN_USERNAME.")
    if existing:
     cur.execute("UPDATE users SET password_hash=%s WHERE id=%s",(pw_hash,existing["id"]))
    else:
     cur.execute("INSERT INTO users(username,email,display_name,faction,password_hash,role) VALUES(%s,%s,'Tournament Administrator','Administration',%s,'admin')",(username,username+"@admin.local.invalid",pw_hash))
    c.commit()
   finally:cur.close();c.close()
  _ready=True
def query(sql,args=(),one=False):
 init();c=connect()
 try:
  cur=c.cursor(dictionary=True);cur.execute(sql,args);r=cur.fetchone() if one else cur.fetchall();cur.close();return r
 finally:c.close()
def mutate(sql,args=()):
 init();c=connect()
 try:
  cur=c.cursor();cur.execute(sql,args);r=cur.lastrowid;c.commit();cur.close();return r
 except:c.rollback();raise
 finally:c.close()
def tournaments():return query("SELECT t.*,COUNT(g.id) game_count FROM tournaments t LEFT JOIN games g ON g.tournament_id=t.id GROUP BY t.id ORDER BY t.created_at DESC")
def games():return query("""SELECT g.*,t.name tournament,t.registration_closes_at,COUNT(DISTINCT c.user_id) enrolled,g.capacity-COUNT(DISTINCT c.user_id) seats_left FROM games g JOIN tournaments t ON t.id=g.tournament_id LEFT JOIN game_choices c ON c.game_id=g.id GROUP BY g.id ORDER BY g.starts_at""")
def choices(user_id=None):
 sql="""SELECT c.user_id,c.game_id,g.name game,g.category,g.rounds,g.starts_at,g.venue,g.capacity,t.name tournament,u.display_name,u.faction FROM game_choices c JOIN games g ON g.id=c.game_id JOIN tournaments t ON t.id=g.tournament_id JOIN users u ON u.id=c.user_id"""
 return query(sql+(" WHERE c.user_id=%s" if user_id else "")+" ORDER BY g.starts_at",(user_id,) if user_id else ())
def leaderboard(faction=False,tournament_id=None):
 results_join="LEFT JOIN results r ON r.participant_id=u.id"
 args=()
 if tournament_id is not None:
  results_join="LEFT JOIN results r ON r.participant_id=u.id AND r.game_id IN (SELECT id FROM games WHERE tournament_id=%s)"
  args=(int(tournament_id),)
 if faction:
  return query(f"""SELECT u.faction,COUNT(DISTINCT u.id) participants,COALESCE(SUM(r.points_awarded),0) points,COUNT(r.id) entries FROM users u {results_join} WHERE u.role='student' GROUP BY u.faction ORDER BY points DESC,u.faction""",args)
 return query(f"""SELECT u.id user_id,u.display_name,u.faction,COALESCE(SUM(r.points_awarded),0) points,COALESCE(SUM(r.placement=1),0) first_places,COALESCE(SUM(r.placement=2),0) second_places,COUNT(r.id) entries FROM users u {results_join} WHERE u.role='student' GROUP BY u.id,u.display_name,u.faction ORDER BY points DESC,first_places DESC,u.display_name""",args)
def game_leaderboard(game_id):
 return query("""SELECT u.id user_id,u.display_name,u.faction,COALESCE(SUM(r.score),0) score,COALESCE(SUM(r.points_awarded),0) points,COALESCE(SUM(r.placement=1),0) first_places,COALESCE(SUM(r.placement=2),0) second_places,COUNT(r.id) entries FROM game_choices c JOIN users u ON u.id=c.user_id LEFT JOIN results r ON r.participant_id=u.id AND r.game_id=c.game_id WHERE c.game_id=%s AND u.role='student' GROUP BY u.id,u.display_name,u.faction ORDER BY score DESC,points DESC,u.display_name""",(game_id,))
def _text(value,label,maximum,required=True):
 value=str(value or "").strip()
 if required and not value:raise ValueError(label+" is required.")
 if len(value)>maximum:raise ValueError(label+" must be "+str(maximum)+" characters or fewer.")
 if any(ord(ch)<32 for ch in value):raise ValueError(label+" contains unsupported characters.")
 return value
def _date(value,label,required=True):
 if value in (None,""):
  if required:raise ValueError(label+" is required.")
  return None
 try:
  parsed=value if isinstance(value,datetime) else datetime.fromisoformat(str(value).replace("T"," "))
 except (TypeError,ValueError):raise ValueError("Enter a valid "+label+".")
 if parsed.tzinfo:parsed=parsed.astimezone(timezone.utc).replace(tzinfo=None)
 return parsed
def _integer(value,label,default=None):
 if value is None or value=="":
  if default is not None:return default
  raise ValueError(label+" is required.")
 if isinstance(value,bool) or isinstance(value,float) and not value.is_integer() or isinstance(value,str) and not re.fullmatch(r"-?[0-9]+",value.strip()):raise ValueError(label+" must be a whole number.")
 try:return int(value)
 except (TypeError,ValueError):raise ValueError(label+" must be a whole number.")
def _rules(p):
 vals=[_integer(p.get(k), "Scoring points", default) for k,default in (("points_first",10),("points_second",7),("points_third",5),("points_participation",1))]
 if any(v<0 or v>10000 for v in vals):raise ValueError("Scoring points must be between 0 and 10,000.")
 if vals != sorted(vals,reverse=True):raise ValueError("Points must decrease from first place to participation.")
 return vals
def create_tournament(p):
 name=_text(p.get("name"),"Tournament name",120)
 description=_text(p.get("description",""),"Description",500,False)
 closing=_date(p.get("registration_closes_at"),"registration closing time",False)
 first,second,third,participation=_rules(p)
 return mutate("INSERT INTO tournaments(name,description,registration_closes_at,points_first,points_second,points_third,points_participation) VALUES(%s,%s,%s,%s,%s,%s,%s)",(name,description,closing,first,second,third,participation))
def update_tournament(tid,p):
 name=_text(p.get("name"),"Tournament name",120)
 description=_text(p.get("description",""),"Description",500,False)
 closing=_date(p.get("registration_closes_at"),"registration closing time",False)
 first,second,third,participation=_rules(p)
 init();c=connect()
 try:
  cur=c.cursor(dictionary=True);cur.execute("SELECT id,points_first,points_second,points_third,points_participation FROM tournaments WHERE id=%s FOR UPDATE",(tid,))
  current=cur.fetchone()
  if not current:raise ValueError("This tournament no longer exists.")
  cur.execute("SELECT COUNT(*) n FROM results r JOIN games g ON g.id=r.game_id WHERE g.tournament_id=%s",(tid,))
  if cur.fetchone()["n"] and (first,second,third,participation)!=(current["points_first"],current["points_second"],current["points_third"],current["points_participation"]):raise ValueError("Scoring rules cannot be changed after results are entered. Keep published scores consistent.")
  cur.execute("UPDATE tournaments SET name=%s,description=%s,registration_closes_at=%s,points_first=%s,points_second=%s,points_third=%s,points_participation=%s WHERE id=%s",(name,description,closing,first,second,third,participation,tid))
  c.commit()
 except:c.rollback();raise
 finally:c.close()
def delete_tournament(tid):
 init();c=connect()
 try:
  cur=c.cursor();cur.execute("SELECT id FROM tournaments WHERE id=%s FOR UPDATE",(tid,))
  if not cur.fetchone():raise ValueError("This tournament no longer exists.")
  cur.execute("SELECT COUNT(*) FROM results r JOIN games g ON g.id=r.game_id WHERE g.tournament_id=%s",(tid,))
  if cur.fetchone()[0]:raise ValueError("This tournament has published results and cannot be deleted. Keep it so the standings and audit history remain available.")
  cur.execute("SELECT id FROM games WHERE tournament_id=%s FOR UPDATE",(tid,));game_ids=[row[0] for row in cur.fetchall()]
  if game_ids:
   marks=",".join(["%s"]*len(game_ids))
   cur.execute(f"DELETE FROM results WHERE game_id IN ({marks})",game_ids)
   cur.execute(f"DELETE FROM game_choices WHERE game_id IN ({marks})",game_ids)
   cur.execute(f"DELETE FROM games WHERE id IN ({marks})",game_ids)
  cur.execute("DELETE FROM tournaments WHERE id=%s",(tid,));c.commit()
 except:c.rollback();raise
 finally:c.close()
def _game_values(p):
 name=_text(p.get("name"),"Game name",100)
 venue=_text(p.get("venue"),"Place",160)
 category=_text(p.get("category",""),"Category",80,False)
 tournament_id=_integer(p.get("tournament_id"),"Tournament",0);capacity=_integer(p.get("capacity"),"Participant limit",0);rounds=_integer(p.get("rounds"),"Rounds",1);duration=_integer(p.get("duration_minutes"),"Duration",60)
 starts_at=_date(p.get("starts_at"),"game date and time")
 if not 1<=capacity<=5000:raise ValueError("Participant limit must be between 1 and 5,000.")
 if not 1<=rounds<=20:raise ValueError("Rounds must be between 1 and 20.")
 if not 5<=duration<=1440:raise ValueError("Game duration must be between 5 minutes and 24 hours.")
 return tournament_id,name,category,rounds,starts_at,duration,venue,capacity
def _check_venue_conflict(cur,venue,starts_at,duration,exclude_id=None):
 cur.execute("SELECT id,name,starts_at,duration_minutes FROM games WHERE LOWER(TRIM(venue))=LOWER(TRIM(%s))",(venue,))
 new_end=starts_at+timedelta(minutes=duration)
 for row in cur.fetchall():
  if exclude_id is not None and int(row[0])==int(exclude_id):continue
  old_start=row[2] if isinstance(row[2],datetime) else datetime.fromisoformat(str(row[2]))
  if starts_at < old_start+timedelta(minutes=int(row[3])) and old_start < new_end:
   raise ValueError("This place is already booked for "+str(row[1])+" at that time.")
def create_game(p):
 init();values=_game_values(p);tournament_id,name,category,rounds,starts_at,duration,venue,capacity=values
 c=connect()
 try:
  cur=c.cursor();cur.execute("SELECT id FROM tournaments WHERE id=%s",(tournament_id,))
  if not cur.fetchone():raise ValueError("Choose an existing tournament.")
  _check_venue_conflict(cur,venue,starts_at,duration)
  cur.execute("INSERT INTO games(tournament_id,name,category,rounds,starts_at,duration_minutes,venue,capacity) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",values)
  result=cur.lastrowid;c.commit();return result
 except:c.rollback();raise
 finally:c.close()
def update_game(gid,p):
 init();values=_game_values(p);tournament_id,name,category,rounds,starts_at,duration,venue,capacity=values
 c=connect()
 try:
  cur=c.cursor(dictionary=True);cur.execute("SELECT id,tournament_id FROM games WHERE id=%s FOR UPDATE",(gid,))
  current=cur.fetchone()
  if not current:raise ValueError("This game no longer exists.")
  cur.execute("SELECT COUNT(*) enrolled FROM game_choices WHERE game_id=%s",(gid,));enrolled=cur.fetchone()["enrolled"]
  if capacity<enrolled:raise ValueError("Participant limit cannot be lower than current registrations.")
  cur.execute("SELECT MAX(round_number) max_round FROM results WHERE game_id=%s",(gid,));max_round=cur.fetchone()["max_round"]
  if max_round and rounds<int(max_round):raise ValueError("This game already has results for a later round. Keep at least that many rounds.")
  if max_round and tournament_id!=int(current["tournament_id"]):raise ValueError("A game with published results cannot be moved to another tournament.")
  cur.execute("SELECT id FROM tournaments WHERE id=%s",(tournament_id,))
  if not cur.fetchone():raise ValueError("Choose an existing tournament.")
  _check_venue_conflict(cur,venue,starts_at,duration,gid)
  cur.execute("UPDATE games SET tournament_id=%s,name=%s,category=%s,rounds=%s,starts_at=%s,duration_minutes=%s,venue=%s,capacity=%s WHERE id=%s",(*values,gid))
  c.commit()
 except:c.rollback();raise
 finally:c.close()
def delete_game(gid):
 init();c=connect()
 try:
  cur=c.cursor();cur.execute("SELECT id FROM games WHERE id=%s FOR UPDATE",(gid,))
  if not cur.fetchone():raise ValueError("This game no longer exists.")
  cur.execute("SELECT COUNT(*) FROM results WHERE game_id=%s",(gid,))
  if cur.fetchone()[0]:raise ValueError("This game has published results and cannot be deleted. Keep it so standings and audit history remain available.")
  cur.execute("DELETE FROM game_choices WHERE game_id=%s",(gid,))
  cur.execute("DELETE FROM games WHERE id=%s",(gid,));c.commit()
 except:c.rollback();raise
 finally:c.close()
def students():
 return query("SELECT u.id,u.username,u.email,u.display_name name,u.faction,u.is_active,COUNT(c.game_id) game_count,COALESCE(GROUP_CONCAT(g.name ORDER BY g.starts_at SEPARATOR ', '),'') games FROM users u LEFT JOIN game_choices c ON c.user_id=u.id LEFT JOIN games g ON g.id=c.game_id WHERE u.role='student' GROUP BY u.id,u.username,u.email,u.display_name,u.faction,u.is_active ORDER BY u.is_active DESC,u.display_name")
def delete_participant(uid):
 set_participant_active(uid,False)
def set_participant_active(uid,active):
 init();c=connect()
 try:
  cur=c.cursor();cur.execute("SELECT role,is_active FROM users WHERE id=%s FOR UPDATE",(uid,));row=cur.fetchone()
  if not row or row[0]!="student":raise ValueError("This participant no longer exists.")
  if not active and row[1]:
   cur.execute("DELETE FROM sessions WHERE user_id=%s",(uid,))
  cur.execute("UPDATE users SET is_active=%s WHERE id=%s AND role='student'",(1 if active else 0,uid));c.commit()
 except:c.rollback();raise
 finally:c.close()
def enroll(uid,ids):
 init();c=connect()
 try:
  cur=c.cursor(dictionary=True)
  cur.execute("SELECT id,is_active FROM users WHERE id=%s FOR UPDATE",(uid,));user=cur.fetchone()
  if not user or not user["is_active"]:raise ValueError("Student account not found.")
  cur.execute("SELECT COUNT(*) n FROM game_choices WHERE user_id=%s",(uid,))
  if cur.fetchone()["n"]:raise ValueError("Your game choices were already submitted and cannot be edited.")
  if not 1<=len(ids)<=5 or len(set(ids))!=len(ids):raise ValueError("Choose between 1 and 5 different games.")
  selected=[];now=datetime.now(timezone.utc).replace(tzinfo=None)
  for gid in ids:
   cur.execute("SELECT g.id,g.capacity,g.starts_at,g.duration_minutes,t.registration_closes_at FROM games g JOIN tournaments t ON t.id=g.tournament_id WHERE g.id=%s FOR UPDATE",(gid,));game=cur.fetchone()
   if not game:raise ValueError("A selected game is unavailable.")
   start=game["starts_at"] if isinstance(game["starts_at"],datetime) else datetime.fromisoformat(str(game["starts_at"]))
   closing=game["registration_closes_at"]
   if start<=now:raise ValueError("Registration is closed because a selected game has already started.")
   if closing and closing<=now:raise ValueError("Registration for a selected game has closed.")
   cur.execute("SELECT COUNT(*) n FROM game_choices WHERE game_id=%s",(gid,))
   if cur.fetchone()["n"]>=game["capacity"]:raise ValueError("A selected game has reached its participant limit.")
   selected.append((int(gid),start,start+timedelta(minutes=int(game["duration_minutes"]))))
  for i,one in enumerate(selected):
   for two in selected[i+1:]:
    if one[1]<two[2] and two[1]<one[2]:raise ValueError("Your selected games overlap. Choose games with different times.")
  cur.executemany("INSERT INTO game_choices(user_id,game_id) VALUES(%s,%s)",[(uid,gid) for gid in ids]);c.commit()
 except:c.rollback();raise
 finally:c.close()
def create_user(p,pw):return mutate("INSERT INTO users(username,email,display_name,faction,password_hash,role) VALUES(%s,%s,%s,%s,%s,'student')",(p["username"],p["email"],p["name"],p["faction"],pw))
def user_by_username(u):return query("SELECT * FROM users WHERE username=%s AND is_active=1",(u,),True)
def user_by_id(uid):return query("SELECT id,username,email,display_name name,faction,role FROM users WHERE id=%s AND is_active=1",(uid,),True)
def save_session(token,uid,expires):mutate("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(%s,%s,%s)",(token,uid,expires))
def session_user(token):return query("SELECT u.id,u.username,u.email,u.display_name name,u.faction,u.role FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=%s AND s.expires_at>UTC_TIMESTAMP() AND u.is_active=1",(token,),True)
def delete_session(token):mutate("DELETE FROM sessions WHERE token_hash=%s",(token,))
def participants():
 return query("""SELECT u.id,u.display_name name,u.faction,u.username,c.game_id,g.name game FROM users u JOIN game_choices c ON c.user_id=u.id JOIN games g ON g.id=c.game_id WHERE u.role='student' ORDER BY u.display_name""")
def results(game_id=None,round_no=None):
 sql="""SELECT r.id,r.game_id,g.name game,t.id tournament_id,t.name tournament,r.round_number,u.id participant_id,u.display_name name,u.faction,r.score,r.points_awarded,r.result_status,r.placement,r.created_at FROM results r JOIN games g ON g.id=r.game_id JOIN tournaments t ON t.id=g.tournament_id JOIN users u ON u.id=r.participant_id"""
 filters=[];args=[]
 if game_id is not None:filters.append("r.game_id=%s");args.append(int(game_id))
 if round_no is not None:filters.append("r.round_number=%s");args.append(int(round_no))
 if filters:sql+=" WHERE "+" AND ".join(filters)
 return query(sql+" ORDER BY r.created_at DESC",tuple(args))
def result_audit(game_id):
 return query("""SELECT a.id,a.round_number,a.participant_id,a.action,a.before_values,a.after_values,a.created_at,u.display_name actor FROM result_audit a LEFT JOIN users u ON u.id=a.actor_user_id WHERE a.game_id=%s ORDER BY a.created_at DESC LIMIT 200""",(int(game_id),))
def record_results(game_id,round_no,entries,actor_id):
 try:game_id=_integer(game_id,"Game");round_no=_integer(round_no,"Round")
 except (TypeError,ValueError):raise ValueError("Choose a valid game and round.")
 if not isinstance(entries,list) or not entries:raise ValueError("Add the result for every registered participant.")
 init();c=connect()
 try:
  cur=c.cursor(dictionary=True)
  cur.execute("SELECT g.rounds,t.points_first,t.points_second,t.points_third,t.points_participation FROM games g JOIN tournaments t ON t.id=g.tournament_id WHERE g.id=%s FOR UPDATE",(game_id,))
  game=cur.fetchone()
  if not game:raise ValueError("This game no longer exists.")
  if not 1<=round_no<=int(game["rounds"]):raise ValueError("Choose a round that exists for this game.")
  cur.execute("SELECT user_id FROM game_choices WHERE game_id=%s ORDER BY user_id FOR UPDATE",(game_id,))
  enrolled={int(row["user_id"]) for row in cur.fetchall()}
  normalized=[]
  seen=set()
  for entry in entries:
   try:
    pid=_integer(entry.get("participant_id"),"Participant");score=_integer(entry.get("score"),"Score",0)
   except (TypeError,ValueError,AttributeError):raise ValueError("Enter whole-number scores and valid participants.")
   status=str(entry.get("status","played"))
   place=entry.get("placement")
   try:place=_integer(place,"Place") if place not in (None,"") else None
   except (TypeError,ValueError):raise ValueError("Placements must be whole numbers.")
   if pid in seen:raise ValueError("A participant appears more than once.")
   seen.add(pid)
   if status not in ("played","no_show","disqualified"):raise ValueError("Choose a valid result status.")
   if score<0 or score>2147483647:raise ValueError("Scores must be between 0 and 2,147,483,647.")
   normalized.append({"participant_id":pid,"score":score,"placement":place,"status":status})
  if seen!=enrolled:raise ValueError("Include every registered participant exactly once.")
  played=[x for x in normalized if x["status"]=="played"]
  for item in normalized:
   if item["status"]=="played":
    if item["placement"] is None or not 1<=item["placement"]<=len(played):raise ValueError("Every player who competed needs a valid place.")
   elif item["placement"] is not None or item["score"]!=0:
    raise ValueError("No-shows and disqualified participants must have no place and a score of 0.")
  points={1:int(game["points_first"]),2:int(game["points_second"]),3:int(game["points_third"])}
  for item in normalized:
   place=item["placement"];item["points_awarded"]=(0 if item["status"]!="played" else points.get(place,int(game["points_participation"])))
   cur.execute("SELECT id,score,points_awarded,result_status,placement FROM results WHERE game_id=%s AND round_number=%s AND participant_id=%s FOR UPDATE",(game_id,round_no,item["participant_id"]))
   old=cur.fetchone()
   before={k:old[k] for k in ("score","points_awarded","result_status","placement")} if old else None
   after={"score":item["score"],"points_awarded":item["points_awarded"],"result_status":item["status"],"placement":item["placement"]}
   if old:
    cur.execute("UPDATE results SET score=%s,points_awarded=%s,result_status=%s,placement=%s,created_at=CURRENT_TIMESTAMP WHERE id=%s",(item["score"],item["points_awarded"],item["status"],item["placement"],old["id"]))
    action="updated"
   else:
    cur.execute("INSERT INTO results(game_id,round_number,participant_id,score,points_awarded,result_status,placement) VALUES(%s,%s,%s,%s,%s,%s,%s)",(game_id,round_no,item["participant_id"],item["score"],item["points_awarded"],item["status"],item["placement"]))
    action="created"
   cur.execute("INSERT INTO result_audit(game_id,round_number,participant_id,actor_user_id,action,before_values,after_values) VALUES(%s,%s,%s,%s,%s,%s,%s)",(game_id,round_no,item["participant_id"],actor_id,action,json.dumps(before),json.dumps(after)))
  c.commit()
 except:c.rollback();raise
 finally:c.close()
