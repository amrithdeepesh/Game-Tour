"""MySQL persistence layer; creates empty app tables and optional configured admin only."""
import os,threading,secrets,hashlib
from pathlib import Path
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
  """CREATE TABLE IF NOT EXISTS users(id BIGINT AUTO_INCREMENT PRIMARY KEY,username VARCHAR(40) NOT NULL UNIQUE,email VARCHAR(254) NOT NULL UNIQUE,display_name VARCHAR(120) NOT NULL,faction VARCHAR(80) NOT NULL,password_hash VARCHAR(256) NOT NULL,role ENUM('admin','student') NOT NULL DEFAULT 'student',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS tournaments(id BIGINT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(120) NOT NULL,description VARCHAR(500) NOT NULL DEFAULT '',starts_at DATETIME NULL,ends_at DATETIME NULL,status ENUM('upcoming','active','completed') NOT NULL DEFAULT 'upcoming',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS games(id BIGINT AUTO_INCREMENT PRIMARY KEY,tournament_id BIGINT NOT NULL,name VARCHAR(100) NOT NULL,category VARCHAR(80) NOT NULL DEFAULT '',rounds INT NOT NULL DEFAULT 1,starts_at DATETIME NOT NULL,venue VARCHAR(160) NOT NULL,capacity INT NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,INDEX(tournament_id,starts_at),CONSTRAINT fk_game_tournament FOREIGN KEY(tournament_id) REFERENCES tournaments(id)) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS game_choices(user_id BIGINT NOT NULL,game_id BIGINT NOT NULL,chosen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(user_id,game_id),INDEX(game_id),CONSTRAINT fk_choice_user FOREIGN KEY(user_id) REFERENCES users(id),CONSTRAINT fk_choice_game FOREIGN KEY(game_id) REFERENCES games(id)) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS results(id BIGINT AUTO_INCREMENT PRIMARY KEY,game_id BIGINT NOT NULL,round_number INT NOT NULL,participant_id BIGINT NOT NULL,score INT NOT NULL DEFAULT 0,placement INT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,INDEX(game_id,placement),CONSTRAINT fk_result_game FOREIGN KEY(game_id) REFERENCES games(id),CONSTRAINT fk_result_user FOREIGN KEY(participant_id) REFERENCES users(id)) ENGINE=InnoDB""",
  """CREATE TABLE IF NOT EXISTS sessions(token_hash CHAR(64) PRIMARY KEY,user_id BIGINT NOT NULL,expires_at DATETIME NOT NULL,CONSTRAINT fk_session_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE) ENGINE=InnoDB"""]
  try:
   cur=c.cursor()
   for sql in schema:cur.execute(sql)
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
def games():return query("""SELECT g.*,t.name tournament,COUNT(DISTINCT c.user_id) enrolled,g.capacity-COUNT(DISTINCT c.user_id) seats_left FROM games g JOIN tournaments t ON t.id=g.tournament_id LEFT JOIN game_choices c ON c.game_id=g.id GROUP BY g.id ORDER BY g.starts_at""")
def choices(user_id=None):
 sql="""SELECT c.user_id,c.game_id,g.name game,g.category,g.rounds,g.starts_at,g.venue,g.capacity,t.name tournament,u.display_name,u.faction FROM game_choices c JOIN games g ON g.id=c.game_id JOIN tournaments t ON t.id=g.tournament_id JOIN users u ON u.id=c.user_id"""
 return query(sql+(" WHERE c.user_id=%s" if user_id else "")+" ORDER BY g.starts_at",(user_id,) if user_id else ())
def leaderboard(faction=False):
 if faction:
  return query("""SELECT u.faction,COUNT(DISTINCT u.id) participants,COALESCE(SUM(r.score),0) points,COUNT(r.id) entries FROM users u LEFT JOIN results r ON r.participant_id=u.id WHERE u.role='student' GROUP BY u.faction ORDER BY points DESC,u.faction""")
 return query("""SELECT u.id user_id,u.display_name,u.faction,COALESCE(SUM(r.score),0) points,COALESCE(SUM(r.placement=1),0) first_places,COALESCE(SUM(r.placement=2),0) second_places,COUNT(r.id) entries FROM users u LEFT JOIN results r ON r.participant_id=u.id WHERE u.role='student' GROUP BY u.id,u.display_name,u.faction ORDER BY points DESC,first_places DESC,u.display_name""")
def game_leaderboard(game_id):
 return query("""SELECT u.id user_id,u.display_name,u.faction,COALESCE(SUM(r.score),0) points,COALESCE(SUM(r.placement=1),0) first_places,COALESCE(SUM(r.placement=2),0) second_places,COUNT(r.id) entries FROM game_choices c JOIN users u ON u.id=c.user_id LEFT JOIN results r ON r.participant_id=u.id AND r.game_id=c.game_id WHERE c.game_id=%s AND u.role='student' GROUP BY u.id,u.display_name,u.faction ORDER BY points DESC,first_places DESC,u.display_name""",(game_id,))
def create_tournament(p):return mutate("INSERT INTO tournaments(name,description,starts_at,ends_at,status) VALUES(%s,%s,%s,%s,%s)",(p["name"],p.get("description",""),p.get("starts_at") or None,p.get("ends_at") or None,p.get("status","upcoming")))
def update_tournament(tid,p):
 name=str(p.get("name","")).strip()
 if not name:raise ValueError("Enter a tournament name.")
 init();c=connect()
 try:
  cur=c.cursor();cur.execute("SELECT id FROM tournaments WHERE id=%s FOR UPDATE",(tid,))
  if not cur.fetchone():raise ValueError("This tournament no longer exists.")
  cur.execute("UPDATE tournaments SET name=%s,description=%s WHERE id=%s",(name,str(p.get("description","")).strip(),tid))
  c.commit()
 except:c.rollback();raise
 finally:c.close()
def delete_tournament(tid):
 init();c=connect()
 try:
  cur=c.cursor();cur.execute("SELECT id FROM tournaments WHERE id=%s FOR UPDATE",(tid,))
  if not cur.fetchone():raise ValueError("This tournament no longer exists.")
  cur.execute("SELECT id FROM games WHERE tournament_id=%s FOR UPDATE",(tid,));game_ids=[row[0] for row in cur.fetchall()]
  if game_ids:
   marks=",".join(["%s"]*len(game_ids))
   cur.execute(f"DELETE FROM results WHERE game_id IN ({marks})",game_ids)
   cur.execute(f"DELETE FROM game_choices WHERE game_id IN ({marks})",game_ids)
   cur.execute(f"DELETE FROM games WHERE id IN ({marks})",game_ids)
  cur.execute("DELETE FROM tournaments WHERE id=%s",(tid,));c.commit()
 except:c.rollback();raise
 finally:c.close()
def create_game(p):return mutate("INSERT INTO games(tournament_id,name,category,rounds,starts_at,venue,capacity) VALUES(%s,%s,%s,%s,%s,%s,%s)",(p["tournament_id"],p["name"],p.get("category",""),p.get("rounds",1),p["starts_at"],p["venue"],p["capacity"]))
def update_game(gid,p):
 name=str(p.get("name","")).strip();venue=str(p.get("venue","")).strip()
 capacity=int(p.get("capacity",0));starts_at=p.get("starts_at")
 if not name or not venue or not starts_at:raise ValueError("Enter a game name, date and time, and place.")
 if capacity<1:raise ValueError("The participant limit must be at least one.")
 init();c=connect()
 try:
  cur=c.cursor(dictionary=True);cur.execute("SELECT id FROM games WHERE id=%s FOR UPDATE",(gid,));row=cur.fetchone()
  if not row:raise ValueError("This game no longer exists.")
  cur.execute("SELECT COUNT(*) enrolled FROM game_choices WHERE game_id=%s",(gid,));enrolled=cur.fetchone()["enrolled"]
  if capacity<enrolled:raise ValueError("The participant limit cannot be lower than current registrations.")
  tournament_id=int(p.get("tournament_id",0))
  cur.execute("SELECT id FROM tournaments WHERE id=%s",(tournament_id,))
  if not cur.fetchone():raise ValueError("Choose an existing tournament.")
  cur.execute("UPDATE games SET tournament_id=%s,name=%s,category=%s,starts_at=%s,venue=%s,capacity=%s WHERE id=%s",(tournament_id,name,str(p.get("category","")).strip(),starts_at,venue,capacity,gid));c.commit()
 except:c.rollback();raise
 finally:c.close()
def delete_game(gid):
 init();c=connect()
 try:
  cur=c.cursor();cur.execute("SELECT id FROM games WHERE id=%s FOR UPDATE",(gid,))
  if not cur.fetchone():raise ValueError("This game no longer exists.")
  cur.execute("DELETE FROM results WHERE game_id=%s",(gid,))
  cur.execute("DELETE FROM game_choices WHERE game_id=%s",(gid,))
  cur.execute("DELETE FROM games WHERE id=%s",(gid,));c.commit()
 except:c.rollback();raise
 finally:c.close()
def students():
 return query("SELECT u.id,u.username,u.email,u.display_name name,u.faction,COUNT(c.game_id) game_count,COALESCE(GROUP_CONCAT(g.name ORDER BY g.starts_at SEPARATOR ', '),'') games FROM users u LEFT JOIN game_choices c ON c.user_id=u.id LEFT JOIN games g ON g.id=c.game_id WHERE u.role='student' GROUP BY u.id,u.username,u.email,u.display_name,u.faction ORDER BY u.display_name")
def delete_participant(uid):
 init();c=connect()
 try:
  cur=c.cursor();cur.execute("SELECT role FROM users WHERE id=%s FOR UPDATE",(uid,));row=cur.fetchone()
  if not row or row[0]!="student":raise ValueError("This participant no longer exists.")
  cur.execute("DELETE FROM sessions WHERE user_id=%s",(uid,))
  cur.execute("DELETE FROM results WHERE participant_id=%s",(uid,))
  cur.execute("DELETE FROM game_choices WHERE user_id=%s",(uid,))
  cur.execute("DELETE FROM users WHERE id=%s AND role='student'",(uid,));c.commit()
 except:c.rollback();raise
 finally:c.close()
def enroll(uid,ids):
 init();c=connect()
 try:
  cur=c.cursor(dictionary=True)
  cur.execute("SELECT id FROM users WHERE id=%s FOR UPDATE",(uid,))
  if not cur.fetchone():raise ValueError("Student account not found.")
  cur.execute("SELECT COUNT(*) n FROM game_choices WHERE user_id=%s",(uid,))
  if cur.fetchone()["n"]:raise ValueError("Your game choices were already submitted and cannot be edited.")
  if not 1<=len(ids)<=5 or len(set(ids))!=len(ids):raise ValueError("Choose between 1 and 5 different games.")
  for gid in ids:
   cur.execute("SELECT capacity FROM games WHERE id=%s FOR UPDATE",(gid,));g=cur.fetchone()
   if not g:raise ValueError("A selected game is unavailable.")
   cur.execute("SELECT COUNT(*) n FROM game_choices WHERE game_id=%s",(gid,))
   if cur.fetchone()["n"]>=g["capacity"]:raise ValueError("A selected game has reached its participant limit.")
  cur.executemany("INSERT INTO game_choices(user_id,game_id) VALUES(%s,%s)",[(uid,gid) for gid in ids]);c.commit()
 except:c.rollback();raise
 finally:c.close()
def create_user(p,pw):return mutate("INSERT INTO users(username,email,display_name,faction,password_hash,role) VALUES(%s,%s,%s,%s,%s,'student')",(p["username"],p["email"],p["name"],p["faction"],pw))
def user_by_username(u):return query("SELECT * FROM users WHERE username=%s",(u,),True)
def user_by_id(uid):return query("SELECT id,username,email,display_name name,faction,role FROM users WHERE id=%s",(uid,),True)
def save_session(token,uid,expires):mutate("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(%s,%s,%s)",(token,uid,expires))
def session_user(token):return query("SELECT u.id,u.username,u.email,u.display_name name,u.faction,u.role FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=%s AND s.expires_at>NOW()",(token,),True)
def delete_session(token):mutate("DELETE FROM sessions WHERE token_hash=%s",(token,))
def participants():
 return query("""SELECT u.id,u.display_name name,u.faction,u.username,c.game_id,g.name game FROM users u JOIN game_choices c ON c.user_id=u.id JOIN games g ON g.id=c.game_id WHERE u.role='student' ORDER BY u.display_name""")
def results():
 return query("""SELECT r.id,r.game_id,g.name game,r.round_number,u.display_name name,u.faction,r.score,r.placement,r.created_at FROM results r JOIN games g ON g.id=r.game_id JOIN users u ON u.id=r.participant_id ORDER BY r.created_at DESC""")
def record_score(p):
 vals=(int(p["game_id"]),int(p["round"]),int(p["participant_id"]),int(p["score"]),int(p["placement"]) if p.get("placement") else None)
 if vals[1]<1 or vals[3]<0 or (vals[4] is not None and vals[4] not in (1,2,3)):raise ValueError("Enter a round, non-negative score, and optional place 1, 2, or 3.")
 valid=query("SELECT 1 ok FROM game_choices WHERE user_id=%s AND game_id=%s",(vals[2],vals[0]),True)
 if not valid:raise ValueError("Choose a student who is registered for this game.")
 return mutate("INSERT INTO results(game_id,round_number,participant_id,score,placement) VALUES(%s,%s,%s,%s,%s)",vals)

def record_match(p):
 game_id=int(p["game_id"]);round_no=int(p["round"]);winner=int(p["winner_id"]);loser=int(p["loser_id"]);ws=int(p["winner_score"]);ls=int(p["loser_score"])
 if winner==loser:raise ValueError("Winner and runner-up must be different students.")
 if round_no<1 or min(ws,ls)<0:raise ValueError("Round must be positive and scores cannot be negative.")
 init();c=connect()
 try:
  cur=c.cursor(dictionary=True);cur.execute("SELECT user_id FROM game_choices WHERE game_id=%s AND user_id IN (%s,%s) FOR UPDATE",(game_id,winner,loser));ids={r["user_id"] for r in cur.fetchall()}
  if ids!={winner,loser}:raise ValueError("Both students must be registered for the selected game.")
  cur.executemany("INSERT INTO results(game_id,round_number,participant_id,score,placement) VALUES(%s,%s,%s,%s,%s)",[(game_id,round_no,winner,ws,1),(game_id,round_no,loser,ls,2)])
  c.commit()
 except:c.rollback();raise
 finally:c.close()
