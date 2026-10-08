"""MySQL persistence for tournament games, participants, schedules, and results."""
import os
import threading
from contextlib import contextmanager
from pathlib import Path

import mysql.connector

_BASE_GAMES = [
    ("Chess", "Strategy", "Arena Chess Hall", "Individual strategy tournament"),
    ("Badminton", "Racquet", "Court A", "Singles and doubles brackets"),
    ("Table Tennis", "Racquet", "Table Tennis Hall", "Singles tournament"),
]
_BASE_PLAYERS = [
    ("Aarav Sharma", "Red Dragons", "Chess", "aarav@example.edu", 1240, 8),
    ("Mira Patel", "Blue Warriors", "Badminton", "mira@example.edu", 1185, 7),
    ("Kabir Nair", "Green Titans", "Table Tennis", "kabir@example.edu", 1090, 6),
    ("Ananya Rao", "Gold Falcons", "Chess", "ananya@example.edu", 1035, 5),
    ("Ishaan Gupta", "Red Dragons", "Badminton", "ishaan@example.edu", 980, 5),
    ("Diya Menon", "Blue Warriors", "Table Tennis", "diya@example.edu", 925, 4),
]
_BASE_MATCHES = [
    ("Chess · Round 3", "Chess", "Arena Chess Hall", 9, 11),
    ("Badminton · Semi-final", "Badminton", "Court A", 10, 12),
    ("Table Tennis · Final", "Table Tennis", "Table Tennis Hall", 12, 14),
    ("Chess · Final", "Chess", "Arena Chess Hall", 13, 15),
]
_ready = False
_init_lock = threading.Lock()


def _load_local_env():
    """Load backend/.env without overriding OS environment variables."""
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _connect():
    _load_local_env()
    required = ("DB_USER", "DB_PASSWORD", "DB_NAME")
    missing = [key for key in required if key not in os.environ]
    if missing:
        raise RuntimeError("MySQL is not configured. Copy backend/.env.example to backend/.env and set DB_USER, DB_PASSWORD, and DB_NAME.")
    try:
        port = int(os.getenv("DB_PORT", "3306"))
    except ValueError as exc:
        raise RuntimeError("DB_PORT must be a number.") from exc
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=port,
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        connection_timeout=4,
        autocommit=False,
    )


@contextmanager
def _transaction():
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _schema_statements():
    return [
        """CREATE TABLE IF NOT EXISTS tournament_games (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            game_id VARCHAR(20) NULL UNIQUE,
            name VARCHAR(100) NOT NULL UNIQUE,
            category VARCHAR(80) NOT NULL DEFAULT 'Other',
            venue VARCHAR(120) NOT NULL DEFAULT 'Main Arena',
            description VARCHAR(500) NOT NULL DEFAULT '',
            status VARCHAR(20) NOT NULL DEFAULT 'Open',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS tournament_participants (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(20) NULL UNIQUE,
            name VARCHAR(120) NOT NULL,
            faction VARCHAR(100) NOT NULL DEFAULT '',
            game_id VARCHAR(20) NOT NULL,
            email VARCHAR(254) NOT NULL DEFAULT '',
            notes TEXT NOT NULL,
            points INT NOT NULL DEFAULT 0,
            wins INT NOT NULL DEFAULT 0,
            status ENUM('Pending','Active','Declined') NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_tournament_players_game (game_id, status),
            INDEX idx_tournament_players_rank (game_id, points DESC, wins DESC),
            CONSTRAINT fk_tournament_participant_game FOREIGN KEY (game_id)
                REFERENCES tournament_games(game_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS tournament_matches (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(160) NOT NULL,
            game_id VARCHAR(20) NOT NULL,
            arena VARCHAR(120) NOT NULL,
            starts_hour TINYINT UNSIGNED NOT NULL,
            ends_hour TINYINT UNSIGNED NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'Upcoming',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_tournament_schedule (game_id, starts_hour),
            CONSTRAINT fk_tournament_match_game FOREIGN KEY (game_id)
                REFERENCES tournament_games(game_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS tournament_results (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            result_id VARCHAR(20) NULL UNIQUE,
            game_id VARCHAR(20) NOT NULL,
            match_title VARCHAR(160) NOT NULL,
            winner_id VARCHAR(20) NOT NULL,
            loser_id VARCHAR(20) NOT NULL,
            winner_score INT NOT NULL,
            loser_score INT NOT NULL,
            played_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_tournament_results_game (game_id, played_at),
            CONSTRAINT fk_tournament_result_game FOREIGN KEY (game_id)
                REFERENCES tournament_games(game_id),
            CONSTRAINT fk_tournament_result_winner FOREIGN KEY (winner_id)
                REFERENCES tournament_participants(student_id),
            CONSTRAINT fk_tournament_result_loser FOREIGN KEY (loser_id)
                REFERENCES tournament_participants(student_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    ]


def _insert_game(cursor, name, category, venue, description):
    cursor.execute(
        "INSERT INTO tournament_games (name,category,venue,description) VALUES (%s,%s,%s,%s)",
        (name, category, venue, description),
    )
    row_id = cursor.lastrowid
    game_id = f"G{row_id:03d}"
    cursor.execute("UPDATE tournament_games SET game_id=%s WHERE id=%s", (game_id, row_id))
    return game_id


def initialize_database():
    """Create app tables and seed examples only where tables are empty."""
    global _ready
    if _ready:
        return
    with _init_lock:
        if _ready:
            return
        with _transaction() as connection:
            cursor = connection.cursor()
            for statement in _schema_statements():
                cursor.execute(statement)
            counts = {}
            for table in ("tournament_games", "tournament_participants", "tournament_matches", "tournament_results"):
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            # Seed the sample tournament only for a completely fresh app database.
            if not any(counts.values()):
                game_ids = {}
                for game in _BASE_GAMES:
                    game_id = _insert_game(cursor, *game)
                    game_ids[game[0]] = game_id
                for name, faction, game, email, points, wins in _BASE_PLAYERS:
                    cursor.execute(
                        """INSERT INTO tournament_participants
                           (name,faction,game_id,email,notes,points,wins,status)
                           VALUES (%s,%s,%s,%s,'',%s,%s,'Active')""",
                        (name, faction, game_ids[game], email, points, wins),
                    )
                    row_id = cursor.lastrowid
                    cursor.execute(
                        "UPDATE tournament_participants SET student_id=%s WHERE id=%s",
                        (f"ST{row_id:03d}", row_id),
                    )
                for title, game, arena, start, end in _BASE_MATCHES:
                    cursor.execute(
                        """INSERT INTO tournament_matches
                           (title,game_id,arena,starts_hour,ends_hour)
                           VALUES (%s,%s,%s,%s,%s)""",
                        (title, game_ids[game], arena, start, end),
                    )
            cursor.close()
        _ready = True


def _read_all(cursor, sql, args=()):
    cursor.execute(sql, args)
    return cursor.fetchall()


def load_bundle():
    initialize_database()
    connection = _connect()
    try:
        cursor = connection.cursor(dictionary=True)
        games = _read_all(cursor, "SELECT game_id,name,category,venue,description,status FROM tournament_games ORDER BY id")
        players = _read_all(
            cursor,
            """SELECT p.student_id,p.name,p.faction,g.name AS game,p.email,p.notes,
                      p.points,p.wins,p.status
               FROM tournament_participants p JOIN tournament_games g ON g.game_id=p.game_id
               ORDER BY p.id""",
        )
        matches = _read_all(
            cursor,
            """SELECT m.title AS name,g.name AS game,m.arena,m.starts_hour AS start,
                      m.ends_hour AS end,m.status
               FROM tournament_matches m JOIN tournament_games g ON g.game_id=m.game_id
               ORDER BY m.starts_hour,m.id""",
        )
        results = _read_all(
            cursor,
            """SELECT r.result_id,g.name AS game,r.match_title AS match_label,
                      w.student_id AS winner_id,w.name AS winner,r.winner_score,
                      l.student_id AS loser_id,l.name AS loser,r.loser_score,r.played_at
               FROM tournament_results r JOIN tournament_games g ON g.game_id=r.game_id
               JOIN tournament_participants w ON w.student_id=r.winner_id
               JOIN tournament_participants l ON l.student_id=r.loser_id
               ORDER BY r.id DESC""",
        )
        for item in results:
            item["match"] = item.pop("match_label")
        cursor.close()
        return {"games": games, "players": players, "matches": matches, "results": results}
    finally:
        connection.close()


def list_leaderboard(game=None):
    players = load_bundle()["players"]
    ranked = [p for p in players if p["status"] == "Active" and (not game or p["game"] == game)]
    return sorted(ranked, key=lambda p: (-p["points"], -p["wins"], p["name"].casefold()))


def create_game(payload):
    initialize_database()
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("Game name is required.")
    with _transaction() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id FROM tournament_games WHERE name=%s", (name,))
        if cursor.fetchone():
            raise ValueError("That game already exists.")
        cursor.execute(
            "INSERT INTO tournament_games (name,category,venue,description) VALUES (%s,%s,%s,%s)",
            (
                name,
                str(payload.get("category", "Other")).strip() or "Other",
                str(payload.get("venue", "Main Arena")).strip() or "Main Arena",
                str(payload.get("description", "")).strip(),
            ),
        )
        row_id = cursor.lastrowid
        game_id = f"G{row_id:03d}"
        cursor.execute("UPDATE tournament_games SET game_id=%s WHERE id=%s", (game_id, row_id))
        cursor.execute("SELECT game_id,name,category,venue,description,status FROM tournament_games WHERE id=%s", (row_id,))
        item = cursor.fetchone()
        cursor.close()
    return item


def create_participant(payload):
    initialize_database()
    name = str(payload.get("name", "")).strip()
    if not name:
        raise ValueError("Student name is required.")
    with _transaction() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT game_id FROM tournament_games WHERE name=%s", (str(payload.get("game", "")).strip(),))
        game = cursor.fetchone()
        if not game:
            raise ValueError("Choose an available game.")
        cursor.execute(
            """INSERT INTO tournament_participants
               (name,faction,game_id,email,notes,status) VALUES (%s,%s,%s,%s,%s,'Pending')""",
            (
                name,
                str(payload.get("faction", "Open Entry")).strip(),
                game["game_id"],
                str(payload.get("email", "")).strip(),
                str(payload.get("notes", "")).strip(),
            ),
        )
        row_id = cursor.lastrowid
        student_id = f"ST{row_id:03d}"
        cursor.execute("UPDATE tournament_participants SET student_id=%s WHERE id=%s", (student_id, row_id))
        cursor.execute(
            """SELECT p.student_id,p.name,p.faction,g.name AS game,p.email,p.notes,
                      p.points,p.wins,p.status
               FROM tournament_participants p JOIN tournament_games g ON g.game_id=p.game_id
               WHERE p.id=%s""",
            (row_id,),
        )
        item = cursor.fetchone()
        cursor.close()
    return item


def record_result(payload):
    initialize_database()
    game_name = str(payload.get("game", "")).strip()
    winner_id = str(payload.get("winner_id", "")).strip()
    loser_id = str(payload.get("loser_id", "")).strip()
    try:
        winner_score = int(payload.get("winner_score", 0))
        loser_score = int(payload.get("loser_score", 0))
        if min(winner_score, loser_score) < 0:
            raise ValueError
    except (ValueError, TypeError) as exc:
        raise ValueError("Scores must be zero or greater.") from exc
    with _transaction() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT game_id FROM tournament_games WHERE name=%s", (game_name,))
        game = cursor.fetchone()
        if not game:
            raise ValueError("Choose a valid game.")
        cursor.execute(
            """SELECT student_id,name,game_id,status FROM tournament_participants
               WHERE student_id IN (%s,%s) FOR UPDATE""",
            (winner_id, loser_id),
        )
        participants = {p["student_id"]: p for p in cursor.fetchall()}
        winner, loser = participants.get(winner_id), participants.get(loser_id)
        if not winner or not loser or winner_id == loser_id:
            raise ValueError("Choose two different registered participants.")
        if winner["game_id"] != game["game_id"] or loser["game_id"] != game["game_id"]:
            raise ValueError("Both participants must be registered in this game.")
        if winner["status"] != "Active" or loser["status"] != "Active":
            raise ValueError("Both participants must be approved before recording a result.")
        cursor.execute(
            "UPDATE tournament_participants SET points=points+%s,wins=wins+1 WHERE student_id=%s",
            (winner_score, winner_id),
        )
        cursor.execute(
            "UPDATE tournament_participants SET points=points+%s WHERE student_id=%s",
            (loser_score, loser_id),
        )
        match = str(payload.get("match", "Final")).strip() or "Match"
        cursor.execute(
            """INSERT INTO tournament_results
               (game_id,match_title,winner_id,loser_id,winner_score,loser_score)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (game["game_id"], match, winner_id, loser_id, winner_score, loser_score),
        )
        result_db_id = cursor.lastrowid
        result_id = f"R{result_db_id:03d}"
        cursor.execute("UPDATE tournament_results SET result_id=%s WHERE id=%s", (result_id, result_db_id))
        cursor.execute(
            """SELECT r.result_id,g.name AS game,r.match_title AS match_label,
                      r.winner_id,w.name AS winner,r.winner_score,
                      r.loser_id,l.name AS loser,r.loser_score,r.played_at
               FROM tournament_results r JOIN tournament_games g ON g.game_id=r.game_id
               JOIN tournament_participants w ON w.student_id=r.winner_id
               JOIN tournament_participants l ON l.student_id=r.loser_id
               WHERE r.id=%s""",
            (result_db_id,),
        )
        item = cursor.fetchone()
        item["match"] = item.pop("match_label")
        cursor.close()
    return item


def set_participant_status(student_id, status):
    initialize_database()
    if status not in ("Active", "Declined"):
        raise ValueError("Status must be Active or Declined.")
    with _transaction() as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE tournament_participants SET status=%s WHERE student_id=%s", (status, student_id))
        if cursor.rowcount == 0:
            cursor.execute("SELECT id FROM tournament_participants WHERE student_id=%s", (student_id,))
            if not cursor.fetchone():
                raise LookupError("Participant not found.")
        cursor.close()
    return next((p for p in load_bundle()["players"] if p["student_id"] == student_id), None)


def delete_participant(student_id):
    initialize_database()
    with _transaction() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM tournament_participants WHERE student_id=%s", (student_id,))
        if not cursor.fetchone():
            raise LookupError("Participant not found.")
        cursor.execute("DELETE FROM tournament_participants WHERE student_id=%s", (student_id,))
        cursor.close()
    return student_id
