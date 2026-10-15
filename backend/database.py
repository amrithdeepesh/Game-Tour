"""MySQL persistence layer; creates empty app tables and optional configured admin only."""

import hashlib
import json
import os
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import mysql.connector
from mysql.connector import errorcode

_ready = False
_lock = threading.Lock()


def _env():
    p = Path(__file__).with_name(".env")
    if p.exists():
        for line in p.read_text(encoding="utf8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def connect(with_db=True):
    _env()
    if any(not os.getenv(k) for k in ("DB_USER", "DB_PASSWORD", "DB_NAME")):
        raise RuntimeError(
            "MySQL setup required: set DB_USER, DB_PASSWORD, and DB_NAME in backend/.env."
        )
    cfg = dict(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connection_timeout=5,
        autocommit=False,
    )
    if with_db:
        cfg["database"] = os.environ["DB_NAME"]
    return mysql.connector.connect(**cfg)


def init():
    global _ready
    if _ready:
        return
    with _lock:
        if _ready:
            return
        try:
            c = connect()
        except mysql.connector.Error as exc:
            if exc.errno != errorcode.ER_BAD_DB_ERROR:
                raise
            bootstrap = connect(False)
            cur = bootstrap.cursor()
            try:
                db = os.environ["DB_NAME"].replace("`", "")
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                bootstrap.commit()
            finally:
                cur.close()
                bootstrap.close()
            c = connect()
        # Create tables in parent-to-child order so foreign keys can be added safely.
        schema = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(40) NOT NULL UNIQUE,
                email VARCHAR(254) NOT NULL UNIQUE,
                display_name VARCHAR(120) NOT NULL,
                faction VARCHAR(80) NOT NULL,
                password_hash VARCHAR(256) NOT NULL,
                role ENUM('admin', 'student') NOT NULL DEFAULT 'student',
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS tournaments (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                description VARCHAR(500) NOT NULL DEFAULT '',
                starts_at DATETIME NULL,
                ends_at DATETIME NULL,
                registration_closes_at DATETIME NULL,
                points_first INT NOT NULL DEFAULT 10,
                points_second INT NOT NULL DEFAULT 7,
                points_third INT NOT NULL DEFAULT 5,
                points_participation INT NOT NULL DEFAULT 1,
                status ENUM('upcoming', 'active', 'completed')
                    NOT NULL DEFAULT 'upcoming',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS games (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                tournament_id BIGINT NOT NULL,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(80) NOT NULL DEFAULT '',
                rounds INT NOT NULL DEFAULT 1,
                starts_at DATETIME NOT NULL,
                duration_minutes INT NOT NULL DEFAULT 60,
                venue VARCHAR(160) NOT NULL,
                capacity INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX (tournament_id, starts_at),
                CONSTRAINT fk_game_tournament
                    FOREIGN KEY (tournament_id) REFERENCES tournaments(id)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS game_choices (
                user_id BIGINT NOT NULL,
                game_id BIGINT NOT NULL,
                chosen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, game_id),
                INDEX (game_id),
                CONSTRAINT fk_choice_user
                    FOREIGN KEY (user_id) REFERENCES users(id),
                CONSTRAINT fk_choice_game
                    FOREIGN KEY (game_id) REFERENCES games(id)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS results (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                game_id BIGINT NOT NULL,
                round_number INT NOT NULL,
                participant_id BIGINT NOT NULL,
                score INT NOT NULL DEFAULT 0,
                points_awarded INT NOT NULL DEFAULT 0,
                result_status ENUM('played', 'no_show', 'disqualified')
                    NOT NULL DEFAULT 'played',
                placement INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_result_game_round_participant
                    (game_id, round_number, participant_id),
                INDEX (game_id, placement),
                CONSTRAINT fk_result_game
                    FOREIGN KEY (game_id) REFERENCES games(id),
                CONSTRAINT fk_result_user
                    FOREIGN KEY (participant_id) REFERENCES users(id)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash CHAR(64) PRIMARY KEY,
                user_id BIGINT NOT NULL,
                expires_at DATETIME NOT NULL,
                CONSTRAINT fk_session_user
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS result_audit (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                game_id BIGINT NOT NULL,
                round_number INT NOT NULL,
                participant_id BIGINT NOT NULL,
                actor_user_id BIGINT NULL,
                action VARCHAR(20) NOT NULL,
                before_values JSON NULL,
                after_values JSON NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX (game_id, created_at)
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS factions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(80) NOT NULL UNIQUE,
                color VARCHAR(30) NOT NULL DEFAULT '#596fe0',
                motto VARCHAR(255) NOT NULL DEFAULT '',
                badge_icon VARCHAR(40) NOT NULL DEFAULT 'flag',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS waiting_lists (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                game_id BIGINT NOT NULL,
                position INT NOT NULL DEFAULT 1,
                status ENUM('waiting', 'promoted', 'cancelled') NOT NULL DEFAULT 'waiting',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_waiting_user_game (user_id, game_id),
                INDEX (game_id, status, created_at),
                CONSTRAINT fk_wait_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_wait_game FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS matches (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                game_id BIGINT NOT NULL,
                round_number INT NOT NULL DEFAULT 1,
                match_name VARCHAR(160) NOT NULL,
                venue VARCHAR(160) NOT NULL DEFAULT '',
                starts_at DATETIME NOT NULL,
                status ENUM('upcoming', 'ongoing', 'completed') NOT NULL DEFAULT 'upcoming',
                participant1_id BIGINT NULL,
                participant2_id BIGINT NULL,
                score1 INT NOT NULL DEFAULT 0,
                score2 INT NOT NULL DEFAULT 0,
                winner_id BIGINT NULL,
                notes VARCHAR(255) NOT NULL DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX (game_id, starts_at),
                CONSTRAINT fk_match_game FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
                CONSTRAINT fk_match_p1 FOREIGN KEY (participant1_id) REFERENCES users(id) ON DELETE SET NULL,
                CONSTRAINT fk_match_p2 FOREIGN KEY (participant2_id) REFERENCES users(id) ON DELETE SET NULL,
                CONSTRAINT fk_match_win FOREIGN KEY (winner_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS announcements (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(160) NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(60) NOT NULL DEFAULT 'General',
                author_id BIGINT NULL,
                is_pinned TINYINT(1) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_announcement_author FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB
            """,
        ]
        try:
            cur = c.cursor()
            for sql in schema:
                cur.execute(sql)
            migrations = {
                "users": {"is_active": "TINYINT(1) NOT NULL DEFAULT 1"},
                "tournaments": {
                    "registration_closes_at": "DATETIME NULL",
                    "points_first": "INT NOT NULL DEFAULT 10",
                    "points_second": "INT NOT NULL DEFAULT 7",
                    "points_third": "INT NOT NULL DEFAULT 5",
                    "points_participation": "INT NOT NULL DEFAULT 1",
                },
                "games": {"duration_minutes": "INT NOT NULL DEFAULT 60"},
                "results": {
                    "points_awarded": "INT NOT NULL DEFAULT 0",
                    "result_status": "ENUM('played','no_show','disqualified') NOT NULL DEFAULT 'played'",
                },
            }
            for table, columns in migrations.items():
                for column, definition in columns.items():
                    cur.execute(
                        """SELECT 1
FROM information_schema.columns
WHERE table_schema=DATABASE()
    AND TABLE_NAME=%s
    AND COLUMN_NAME=%s""",
                        (table, column),
                    )
                    if not cur.fetchone():
                        cur.execute(
                            f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}"
                        )
                        if table == "results" and column == "points_awarded":
                            cur.execute("""UPDATE results
SET points_awarded=score""")
            cur.execute("""SELECT 1
FROM information_schema.statistics
WHERE table_schema=DATABASE()
    AND TABLE_NAME='results'
    AND index_name='uq_result_game_round_participant'
LIMIT 1""")
            if not cur.fetchone():
                cur.execute(
                    """ALTER TABLE results ADD UNIQUE KEY uq_result_game_round_participant(game_id, round_number, participant_id)"""
                )
            c.commit()
            cur.close()
        finally:
            c.close()
        # Provision exactly one admin only when private credentials were explicitly configured.
        username = os.getenv("ADMIN_USERNAME", "").strip().lower()
        password = os.getenv("ADMIN_PASSWORD", "")
        if username or password:
            if len(username) < 3 or len(password) < 12:
                raise RuntimeError(
                    "Set both ADMIN_USERNAME and a strong ADMIN_PASSWORD (at least 12 characters) in backend/.env."
                )
            salt = secrets.token_bytes(16)
            digest = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt, 240000
            ).hex()
            pw_hash = salt.hex() + ":" + digest
            c = connect()
            cur = c.cursor(dictionary=True)
            try:
                cur.execute(
                    """SELECT id, role AS admin_role
FROM users
WHERE username=%s""",
                    (username,),
                )
                existing = cur.fetchone()
                if existing and existing["admin_role"] != "admin":
                    raise RuntimeError(
                        "Configured admin username already belongs to a student; choose a different ADMIN_USERNAME."
                    )
                if existing:
                    cur.execute(
                        """UPDATE users
SET password_hash=%s
WHERE id=%s""",
                        (pw_hash, existing["id"]),
                    )
                else:
                    cur.execute(
                        """INSERT INTO users(username, email, display_name, faction, password_hash, ROLE)
VALUES(%s,%s,'Tournament Administrator','Administration',%s,'admin')""",
                        (username, username + "@admin.local.invalid", pw_hash),
                    )
                c.commit()
            finally:
                cur.close()
                c.close()

        # Seed default factions and announcements if empty
        seed_conn = connect()
        try:
            scur = seed_conn.cursor(dictionary=True)
            scur.execute("SELECT COUNT(*) n FROM factions")
            if scur.fetchone()["n"] == 0:
                scur.executemany(
                    """INSERT INTO factions(name, color, motto, badge_icon) VALUES(%s, %s, %s, %s)""",
                    [
                        ("Falcons", "#e2b366", "Soaring High with Honor", "zap"),
                        ("Tigers", "#e86363", "Fierce and Relentless", "flame"),
                        ("Sharks", "#596fe0", "Dominating the Depths", "shield"),
                        ("Eagles", "#58c497", "Precision, Strength, Victory", "award"),
                    ],
                )
                seed_conn.commit()

            scur.execute("SELECT COUNT(*) n FROM announcements")
            if scur.fetchone()["n"] == 0:
                scur.executemany(
                    """INSERT INTO announcements(title, content, category, is_pinned) VALUES(%s, %s, %s, %s)""",
                    [
                        (
                            "Welcome to ARENA 2026",
                            "The annual Inter-Faction Sports Meet has begun! Check event schedules, enroll, and cheer for your faction.",
                            "Tournament",
                            1,
                        ),
                        (
                            "Track & Field Heat Schedule",
                            "100m Sprint heats will start promptly at 09:00 UTC at Track Field. Participants please arrive 15 minutes before.",
                            "Schedule",
                            0,
                        ),
                        (
                            "Live Scoreboard Active",
                            "Match updates and real-time scores are tracked live. Check the Live Games tab for ongoing fixtures.",
                            "Notice",
                            0,
                        ),
                    ],
                )
                seed_conn.commit()

            scur.execute("SELECT COUNT(*) n FROM matches")
            if scur.fetchone()["n"] == 0:
                scur.execute("SELECT id, name, starts_at, venue FROM games LIMIT 3")
                sample_games = scur.fetchall()
                scur.execute("SELECT id, display_name FROM users WHERE role='student' LIMIT 6")
                sample_students = scur.fetchall()
                if len(sample_games) >= 2 and len(sample_students) >= 4:
                    scur.executemany(
                        """INSERT INTO matches(game_id, round_number, match_name, venue, starts_at, status, participant1_id, participant2_id, score1, score2, winner_id, notes)
                        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        [
                            (
                                sample_games[0]["id"],
                                1,
                                f"{sample_games[0]['name']} - Heat 1",
                                sample_games[0]["venue"],
                                sample_games[0]["starts_at"],
                                "ongoing",
                                sample_students[0]["id"],
                                sample_students[1]["id"],
                                11,
                                9,
                                None,
                                "Intense second half! Administrator verified.",
                            ),
                            (
                                sample_games[1]["id"],
                                1,
                                f"{sample_games[1]['name']} - Round 1 Match",
                                sample_games[1]["venue"],
                                sample_games[1]["starts_at"],
                                "upcoming",
                                sample_students[2]["id"],
                                sample_students[3]["id"],
                                0,
                                0,
                                None,
                                "Warm-up in progress. Scheduled to start on time.",
                            ),
                        ],
                    )
                    seed_conn.commit()
            scur.close()
        except:
            pass
        finally:
            seed_conn.close()

        _ready = True


def query(sql, args=(), one=False):
    init()
    c = connect()
    try:
        cur = c.cursor(dictionary=True)
        cur.execute(sql, args)
        r = cur.fetchone() if one else cur.fetchall()
        cur.close()
        return r
    finally:
        c.close()


def mutate(sql, args=()):
    init()
    c = connect()
    try:
        cur = c.cursor()
        cur.execute(sql, args)
        r = cur.lastrowid
        c.commit()
        cur.close()
        return r
    except:
        c.rollback()
        raise
    finally:
        c.close()


def tournaments():
    return query("""SELECT t.*,
       COUNT(g.id) game_count
FROM tournaments t
LEFT JOIN games g ON g.tournament_id=t.id
GROUP BY t.id
ORDER BY t.created_at DESC""")


def games():
    return query("""SELECT g.*,
       t.name tournament,
       t.registration_closes_at,
       COUNT(DISTINCT c.user_id) enrolled,
       g.capacity-COUNT(DISTINCT c.user_id) seats_left
FROM games g
JOIN tournaments t ON t.id=g.tournament_id
LEFT JOIN game_choices c ON c.game_id=g.id
GROUP BY g.id
ORDER BY g.starts_at""")


def choices(user_id=None):
    sql = """SELECT c.user_id,
       c.game_id,
       g.name game,
       g.category,
       g.rounds,
       g.starts_at,
       g.venue,
       g.capacity,
       t.name tournament,
       u.display_name,
       u.faction
FROM game_choices c
JOIN games g ON g.id=c.game_id
JOIN tournaments t ON t.id=g.tournament_id
JOIN users u ON u.id=c.user_id"""
    return query(
        sql + (" WHERE c.user_id=%s" if user_id else "") + " ORDER BY g.starts_at",
        (user_id,) if user_id else (),
    )


def leaderboard(faction=False, tournament_id=None):
    results_join = "LEFT JOIN results r ON r.participant_id=u.id"
    args = ()
    if tournament_id is not None:
        results_join = "LEFT JOIN results r ON r.participant_id=u.id AND r.game_id IN (SELECT id FROM games WHERE tournament_id=%s)"
        args = (int(tournament_id),)
    if faction:
        return query(
            f"""SELECT u.faction,COUNT(DISTINCT u.id) participants,COALESCE(SUM(r.points_awarded),0) points,COUNT(r.id) entries FROM users u {results_join} WHERE u.role='student' GROUP BY u.faction ORDER BY points DESC,u.faction""",
            args,
        )
    return query(
        f"""SELECT u.id user_id,u.display_name,u.faction,COALESCE(SUM(r.points_awarded),0) points,COALESCE(SUM(r.placement=1),0) first_places,COALESCE(SUM(r.placement=2),0) second_places,COUNT(r.id) entries FROM users u {results_join} WHERE u.role='student' GROUP BY u.id,u.display_name,u.faction ORDER BY points DESC,first_places DESC,u.display_name""",
        args,
    )


def game_leaderboard(game_id):
    return query(
        """SELECT u.id user_id,
       u.display_name,
       u.faction,
       COALESCE(SUM(r.score), 0) score,
       COALESCE(SUM(r.points_awarded), 0) points,
       COALESCE(SUM(r.placement=1), 0) first_places,
       COALESCE(SUM(r.placement=2), 0) second_places,
       COUNT(r.id) entries
FROM game_choices c
JOIN users u ON u.id=c.user_id
LEFT JOIN results r ON r.participant_id=u.id
AND r.game_id=c.game_id
WHERE c.game_id=%s
    AND u.role='student'
GROUP BY u.id,
         u.display_name,
         u.faction
ORDER BY score DESC,
         points DESC,
         u.display_name""",
        (game_id,),
    )


def _text(value, label, maximum, required=True):
    value = str(value or "").strip()
    if required and not value:
        raise ValueError(label + " is required.")
    if len(value) > maximum:
        raise ValueError(label + " must be " + str(maximum) + " characters or fewer.")
    if any(ord(ch) < 32 for ch in value):
        raise ValueError(label + " contains unsupported characters.")
    return value


def _date(value, label, required=True):
    if value in (None, ""):
        if required:
            raise ValueError(label + " is required.")
        return None
    try:
        parsed = (
            value
            if isinstance(value, datetime)
            else datetime.fromisoformat(str(value).replace("T", " "))
        )
    except (TypeError, ValueError):
        raise ValueError("Enter a valid " + label + ".")
    if parsed.tzinfo:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _integer(value, label, default=None):
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(label + " is required.")
    if (
        isinstance(value, bool)
        or isinstance(value, float)
        and not value.is_integer()
        or isinstance(value, str)
        and not re.fullmatch(r"-?[0-9]+", value.strip())
    ):
        raise ValueError(label + " must be a whole number.")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(label + " must be a whole number.")


def _rules(p):
    vals = [
        _integer(p.get(k), "Scoring points", default)
        for k, default in (
            ("points_first", 10),
            ("points_second", 7),
            ("points_third", 5),
            ("points_participation", 1),
        )
    ]
    if any(v < 0 or v > 10000 for v in vals):
        raise ValueError("Scoring points must be between 0 and 10,000.")
    if vals != sorted(vals, reverse=True):
        raise ValueError("Points must decrease from first place to participation.")
    return vals


def create_tournament(p):
    name = _text(p.get("name"), "Tournament name", 120)
    description = _text(p.get("description", ""), "Description", 500, False)
    closing = _date(p.get("registration_closes_at"), "registration closing time", False)
    first, second, third, participation = _rules(p)
    return mutate(
        """INSERT INTO tournaments(name, description, registration_closes_at, points_first, points_second, points_third, points_participation)
VALUES(%s,%s,%s,%s,%s,%s,%s)""",
        (name, description, closing, first, second, third, participation),
    )


def update_tournament(tid, p):
    name = _text(p.get("name"), "Tournament name", 120)
    description = _text(p.get("description", ""), "Description", 500, False)
    closing = _date(p.get("registration_closes_at"), "registration closing time", False)
    first, second, third, participation = _rules(p)
    init()
    c = connect()
    try:
        cur = c.cursor(dictionary=True)
        cur.execute(
            """SELECT id,
       points_first,
       points_second,
       points_third,
       points_participation
FROM tournaments
WHERE id=%s
    FOR
    UPDATE""",
            (tid,),
        )
        current = cur.fetchone()
        if not current:
            raise ValueError("This tournament no longer exists.")
        cur.execute(
            """SELECT COUNT(*) n
FROM results r
JOIN games g ON g.id=r.game_id
WHERE g.tournament_id=%s""",
            (tid,),
        )
        if cur.fetchone()["n"] and (first, second, third, participation) != (
            current["points_first"],
            current["points_second"],
            current["points_third"],
            current["points_participation"],
        ):
            raise ValueError(
                "Scoring rules cannot be changed after results are entered. Keep published scores consistent."
            )
        cur.execute(
            """UPDATE tournaments
SET name=%s,
    description=%s,
    registration_closes_at=%s,
    points_first=%s,
    points_second=%s,
    points_third=%s,
    points_participation=%s
WHERE id=%s""",
            (name, description, closing, first, second, third, participation, tid),
        )
        c.commit()
    except:
        c.rollback()
        raise
    finally:
        c.close()


def delete_tournament(tid):
    init()
    c = connect()
    try:
        cur = c.cursor()
        cur.execute(
            """SELECT id
FROM tournaments
WHERE id=%s
    FOR
    UPDATE""",
            (tid,),
        )
        if not cur.fetchone():
            raise ValueError("This tournament no longer exists.")
        cur.execute(
            """SELECT COUNT(*)
FROM results r
JOIN games g ON g.id=r.game_id
WHERE g.tournament_id=%s""",
            (tid,),
        )
        if cur.fetchone()[0]:
            raise ValueError(
                "This tournament has published results and cannot be deleted. Keep it so the standings and audit history remain available."
            )
        cur.execute(
            """SELECT id
FROM games
WHERE tournament_id=%s
    FOR
    UPDATE""",
            (tid,),
        )
        game_ids = [row[0] for row in cur.fetchall()]
        if game_ids:
            marks = ",".join(["%s"] * len(game_ids))
            cur.execute(f"DELETE FROM results WHERE game_id IN ({marks})", game_ids)
            cur.execute(
                f"DELETE FROM game_choices WHERE game_id IN ({marks})", game_ids
            )
            cur.execute(f"DELETE FROM games WHERE id IN ({marks})", game_ids)
        cur.execute(
            """DELETE
FROM tournaments
WHERE id=%s""",
            (tid,),
        )
        c.commit()
    except:
        c.rollback()
        raise
    finally:
        c.close()


def _game_values(p):
    name = _text(p.get("name"), "Game name", 100)
    venue = _text(p.get("venue"), "Place", 160)
    category = _text(p.get("category", ""), "Category", 80, False)
    tournament_id = _integer(p.get("tournament_id"), "Tournament", 0)
    capacity = _integer(p.get("capacity"), "Participant limit", 0)
    rounds = _integer(p.get("rounds"), "Rounds", 1)
    duration = _integer(p.get("duration_minutes"), "Duration", 60)
    starts_at = _date(p.get("starts_at"), "game date and time")
    if not 1 <= capacity <= 5000:
        raise ValueError("Participant limit must be between 1 and 5,000.")
    if not 1 <= rounds <= 20:
        raise ValueError("Rounds must be between 1 and 20.")
    if not 5 <= duration <= 1440:
        raise ValueError("Game duration must be between 5 minutes and 24 hours.")
    return tournament_id, name, category, rounds, starts_at, duration, venue, capacity


def _check_venue_conflict(cur, venue, starts_at, duration, exclude_id=None):
    cur.execute(
        """SELECT id,
       name,
       starts_at,
       duration_minutes
FROM games
WHERE LOWER(TRIM(venue))=LOWER(TRIM(%s))""",
        (venue,),
    )
    new_end = starts_at + timedelta(minutes=duration)
    for row in cur.fetchall():
        if exclude_id is not None and int(row[0]) == int(exclude_id):
            continue
        old_start = (
            row[2]
            if isinstance(row[2], datetime)
            else datetime.fromisoformat(str(row[2]))
        )
        if (
            starts_at < old_start + timedelta(minutes=int(row[3]))
            and old_start < new_end
        ):
            raise ValueError(
                "This place is already booked for " + str(row[1]) + " at that time."
            )


def create_game(p):
    init()
    values = _game_values(p)
    tournament_id, name, category, rounds, starts_at, duration, venue, capacity = values
    c = connect()
    try:
        cur = c.cursor()
        cur.execute(
            """SELECT id
FROM tournaments
WHERE id=%s""",
            (tournament_id,),
        )
        if not cur.fetchone():
            raise ValueError("Choose an existing tournament.")
        _check_venue_conflict(cur, venue, starts_at, duration)
        cur.execute(
            """INSERT INTO games(tournament_id, name, category, rounds, starts_at, duration_minutes, venue, capacity)
VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
            values,
        )
        result = cur.lastrowid
        c.commit()
        return result
    except:
        c.rollback()
        raise
    finally:
        c.close()


def update_game(gid, p):
    init()
    values = _game_values(p)
    tournament_id, name, category, rounds, starts_at, duration, venue, capacity = values
    c = connect()
    try:
        cur = c.cursor(dictionary=True)
        cur.execute(
            """SELECT id,
       tournament_id
FROM games
WHERE id=%s
    FOR
    UPDATE""",
            (gid,),
        )
        current = cur.fetchone()
        if not current:
            raise ValueError("This game no longer exists.")
        cur.execute(
            """SELECT COUNT(*) enrolled
FROM game_choices
WHERE game_id=%s""",
            (gid,),
        )
        enrolled = cur.fetchone()["enrolled"]
        if capacity < enrolled:
            raise ValueError(
                "Participant limit cannot be lower than current registrations."
            )
        cur.execute(
            """SELECT MAX(round_number) max_round
FROM results
WHERE game_id=%s""",
            (gid,),
        )
        max_round = cur.fetchone()["max_round"]
        if max_round and rounds < int(max_round):
            raise ValueError(
                "This game already has results for a later round. Keep at least that many rounds."
            )
        if max_round and tournament_id != int(current["tournament_id"]):
            raise ValueError(
                "A game with published results cannot be moved to another tournament."
            )
        cur.execute(
            """SELECT id
FROM tournaments
WHERE id=%s""",
            (tournament_id,),
        )
        if not cur.fetchone():
            raise ValueError("Choose an existing tournament.")
        _check_venue_conflict(cur, venue, starts_at, duration, gid)
        cur.execute(
            """UPDATE games
SET tournament_id=%s,
    name=%s,
    category=%s,
    rounds=%s,
    starts_at=%s,
    duration_minutes=%s,
    venue=%s,
    capacity=%s
WHERE id=%s""",
            (*values, gid),
        )
        c.commit()
    except:
        c.rollback()
        raise
    finally:
        c.close()


def delete_game(gid):
    init()
    c = connect()
    try:
        cur = c.cursor()
        cur.execute(
            """SELECT id
FROM games
WHERE id=%s
    FOR
    UPDATE""",
            (gid,),
        )
        if not cur.fetchone():
            raise ValueError("This game no longer exists.")
        cur.execute(
            """SELECT COUNT(*)
FROM results
WHERE game_id=%s""",
            (gid,),
        )
        if cur.fetchone()[0]:
            raise ValueError(
                "This game has published results and cannot be deleted. Keep it so standings and audit history remain available."
            )
        cur.execute(
            """DELETE
FROM game_choices
WHERE game_id=%s""",
            (gid,),
        )
        cur.execute(
            """DELETE
FROM games
WHERE id=%s""",
            (gid,),
        )
        c.commit()
    except:
        c.rollback()
        raise
    finally:
        c.close()


def students():
    return query("""SELECT u.id,
       u.username,
       u.email,
       u.display_name name,
       u.faction,
       u.is_active,
       COUNT(c.game_id) game_count,
       COALESCE(GROUP_CONCAT(g.name
                             ORDER BY g.starts_at SEPARATOR ', '), '') games
FROM users u
LEFT JOIN game_choices c ON c.user_id=u.id
LEFT JOIN games g ON g.id=c.game_id
WHERE u.role='student'
GROUP BY u.id,
         u.username,
         u.email,
         u.display_name,
         u.faction,
         u.is_active
ORDER BY u.is_active DESC,
         u.display_name""")


def delete_participant(uid):
    set_participant_active(uid, False)


def set_participant_active(uid, active):
    init()
    c = connect()
    try:
        cur = c.cursor()
        cur.execute(
            """SELECT ROLE,
       is_active
FROM users
WHERE id=%s
    FOR
    UPDATE""",
            (uid,),
        )
        row = cur.fetchone()
        if not row or row[0] != "student":
            raise ValueError("This participant no longer exists.")
        if not active and row[1]:
            cur.execute(
                """DELETE
FROM sessions
WHERE user_id=%s""",
                (uid,),
            )
        cur.execute(
            """UPDATE users
SET is_active=%s
WHERE id=%s
    AND ROLE='student'""",
            (1 if active else 0, uid),
        )
        c.commit()
    except:
        c.rollback()
        raise
    finally:
        c.close()


def enroll(uid, ids):
    init()
    c = connect()
    try:
        cur = c.cursor(dictionary=True)
        cur.execute(
            """SELECT id,
       is_active
FROM users
WHERE id=%s
    FOR
    UPDATE""",
            (uid,),
        )
        user = cur.fetchone()
        if not user or not user["is_active"]:
            raise ValueError("Student account not found.")
        cur.execute(
            """SELECT COUNT(*) n
FROM game_choices
WHERE user_id=%s""",
            (uid,),
        )
        if cur.fetchone()["n"]:
            raise ValueError(
                "Your game choices were already submitted and cannot be edited."
            )
        if not 1 <= len(ids) <= 5 or len(set(ids)) != len(ids):
            raise ValueError("Choose between 1 and 5 different games.")
        selected = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for gid in ids:
            cur.execute(
                """SELECT g.id,
       g.capacity,
       g.starts_at,
       g.duration_minutes,
       t.registration_closes_at
FROM games g
JOIN tournaments t ON t.id=g.tournament_id
WHERE g.id=%s
    FOR
    UPDATE""",
                (gid,),
            )
            game = cur.fetchone()
            if not game:
                raise ValueError("A selected game is unavailable.")
            start = (
                game["starts_at"]
                if isinstance(game["starts_at"], datetime)
                else datetime.fromisoformat(str(game["starts_at"]))
            )
            closing = game["registration_closes_at"]
            if start <= now:
                raise ValueError(
                    "Registration is closed because a selected game has already started."
                )
            if closing and closing <= now:
                raise ValueError("Registration for a selected game has closed.")
            cur.execute(
                """SELECT COUNT(*) n
FROM game_choices
WHERE game_id=%s""",
                (gid,),
            )
            if cur.fetchone()["n"] >= game["capacity"]:
                raise ValueError("A selected game has reached its participant limit.")
            selected.append(
                (
                    int(gid),
                    start,
                    start + timedelta(minutes=int(game["duration_minutes"])),
                )
            )
        for i, one in enumerate(selected):
            for two in selected[i + 1 :]:
                if one[1] < two[2] and two[1] < one[2]:
                    raise ValueError(
                        "Your selected games overlap. Choose games with different times."
                    )
        cur.executemany(
            """INSERT INTO game_choices(user_id, game_id)
VALUES(%s,%s)""",
            [(uid, gid) for gid in ids],
        )
        c.commit()
    except:
        c.rollback()
        raise
    finally:
        c.close()


def create_user(p, pw):
    return mutate(
        """INSERT INTO users(username, email, display_name, faction, password_hash, ROLE)
VALUES(%s,%s,%s,%s,%s,'student')""",
        (p["username"], p["email"], p["name"], p["faction"], pw),
    )


def user_by_username(u):
    return query(
        """SELECT *
FROM users
WHERE username=%s
    AND is_active=1""",
        (u,),
        True,
    )


def user_by_id(uid):
    return query(
        """SELECT id,
       username,
       email,
       display_name name,
       faction,
       ROLE
FROM users
WHERE id=%s
    AND is_active=1""",
        (uid,),
        True,
    )


def save_session(token, uid, expires):
    mutate(
        """INSERT INTO sessions(token_hash, user_id, expires_at)
VALUES(%s,%s,%s)""",
        (token, uid, expires),
    )


def session_user(token):
    return query(
        """SELECT u.id,
       u.username,
       u.email,
       u.display_name name,
       u.faction,
       u.role
FROM sessions s
JOIN users u ON u.id=s.user_id
WHERE s.token_hash=%s
    AND s.expires_at>UTC_TIMESTAMP()
    AND u.is_active=1""",
        (token,),
        True,
    )


def delete_session(token):
    mutate(
        """DELETE
FROM sessions
WHERE token_hash=%s""",
        (token,),
    )


def participants():
    return query("""SELECT u.id,
       u.display_name name,
       u.faction,
       u.username,
       c.game_id,
       g.name game
FROM users u
JOIN game_choices c ON c.user_id=u.id
JOIN games g ON g.id=c.game_id
WHERE u.role='student'
ORDER BY u.display_name""")


def results(game_id=None, round_no=None):
    sql = """SELECT r.id,
       r.game_id,
       g.name game,
       t.id tournament_id,
       t.name tournament,
       r.round_number,
       u.id participant_id,
       u.display_name name,
       u.faction,
       r.score,
       r.points_awarded,
       r.result_status,
       r.placement,
       r.created_at
FROM results r
JOIN games g ON g.id=r.game_id
JOIN tournaments t ON t.id=g.tournament_id
JOIN users u ON u.id=r.participant_id"""
    filters = []
    args = []
    if game_id is not None:
        filters.append("r.game_id=%s")
        args.append(int(game_id))
    if round_no is not None:
        filters.append("r.round_number=%s")
        args.append(int(round_no))
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    return query(sql + " ORDER BY r.created_at DESC", tuple(args))


def result_audit(game_id):
    return query(
        """SELECT a.id,
       a.round_number,
       a.participant_id,
       a.action,
       a.before_values,
       a.after_values,
       a.created_at,
       u.display_name actor
FROM result_audit a
LEFT JOIN users u ON u.id=a.actor_user_id
WHERE a.game_id=%s
ORDER BY a.created_at DESC
LIMIT 200""",
        (int(game_id),),
    )


def record_results(game_id, round_no, entries, actor_id):
    try:
        game_id = _integer(game_id, "Game")
        round_no = _integer(round_no, "Round")
    except (TypeError, ValueError):
        raise ValueError("Choose a valid game and round.")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Add the result for every registered participant.")
    init()
    c = connect()
    try:
        cur = c.cursor(dictionary=True)
        cur.execute(
            """SELECT g.rounds,
       t.points_first,
       t.points_second,
       t.points_third,
       t.points_participation
FROM games g
JOIN tournaments t ON t.id=g.tournament_id
WHERE g.id=%s
    FOR
    UPDATE""",
            (game_id,),
        )
        game = cur.fetchone()
        if not game:
            raise ValueError("This game no longer exists.")
        if not 1 <= round_no <= int(game["rounds"]):
            raise ValueError("Choose a round that exists for this game.")
        cur.execute(
            """SELECT user_id
FROM game_choices
WHERE game_id=%s
ORDER BY user_id
FOR
UPDATE""",
            (game_id,),
        )
        enrolled = {int(row["user_id"]) for row in cur.fetchall()}
        normalized = []
        seen = set()
        for entry in entries:
            try:
                pid = _integer(entry.get("participant_id"), "Participant")
                score = _integer(entry.get("score"), "Score", 0)
            except (TypeError, ValueError, AttributeError):
                raise ValueError("Enter whole-number scores and valid participants.")
            status = str(entry.get("status", "played"))
            place = entry.get("placement")
            try:
                place = _integer(place, "Place") if place not in (None, "") else None
            except (TypeError, ValueError):
                raise ValueError("Placements must be whole numbers.")
            if pid in seen:
                raise ValueError("A participant appears more than once.")
            seen.add(pid)
            if status not in ("played", "no_show", "disqualified"):
                raise ValueError("Choose a valid result status.")
            if score < 0 or score > 2147483647:
                raise ValueError("Scores must be between 0 and 2,147,483,647.")
            normalized.append(
                {
                    "participant_id": pid,
                    "score": score,
                    "placement": place,
                    "status": status,
                }
            )
        if seen != enrolled:
            raise ValueError("Include every registered participant exactly once.")
        played = [x for x in normalized if x["status"] == "played"]
        for item in normalized:
            if item["status"] == "played":
                if item["placement"] is None or not 1 <= item["placement"] <= len(
                    played
                ):
                    raise ValueError("Every player who competed needs a valid place.")
            elif item["placement"] is not None or item["score"] != 0:
                raise ValueError(
                    "No-shows and disqualified participants must have no place and a score of 0."
                )
        points = {
            1: int(game["points_first"]),
            2: int(game["points_second"]),
            3: int(game["points_third"]),
        }
        for item in normalized:
            place = item["placement"]
            item["points_awarded"] = (
                0
                if item["status"] != "played"
                else points.get(place, int(game["points_participation"]))
            )
            cur.execute(
                """SELECT id,
       score,
       points_awarded,
       result_status,
       placement
FROM results
WHERE game_id=%s
    AND round_number=%s
    AND participant_id=%s
    FOR
    UPDATE""",
                (game_id, round_no, item["participant_id"]),
            )
            old = cur.fetchone()
            before = (
                {
                    k: old[k]
                    for k in ("score", "points_awarded", "result_status", "placement")
                }
                if old
                else None
            )
            after = {
                "score": item["score"],
                "points_awarded": item["points_awarded"],
                "result_status": item["status"],
                "placement": item["placement"],
            }
            if old:
                cur.execute(
                    """UPDATE results
SET score=%s,
    points_awarded=%s,
    result_status=%s,
    placement=%s,
    created_at=CURRENT_TIMESTAMP
WHERE id=%s""",
                    (
                        item["score"],
                        item["points_awarded"],
                        item["status"],
                        item["placement"],
                        old["id"],
                    ),
                )
                action = "updated"
            else:
                cur.execute(
                    """INSERT INTO results(game_id, round_number, participant_id, score, points_awarded, result_status, placement)
VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        game_id,
                        round_no,
                        item["participant_id"],
                        item["score"],
                        item["points_awarded"],
                        item["status"],
                        item["placement"],
                    ),
                )
                action = "created"
            cur.execute(
                """INSERT INTO result_audit(game_id, round_number, participant_id, actor_user_id, action, before_values, after_values)
VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                (
                    game_id,
                    round_no,
                    item["participant_id"],
                    actor_id,
                    action,
                    json.dumps(before),
                    json.dumps(after),
                ),
            )
        c.commit()
    except:
        c.rollback()
        raise
    finally:
        c.close()


def factions():
    """Retrieve all factions with member counts and aggregated tournament points."""
    init()
    return query(
        """SELECT f.id,
                  f.name,
                  f.color,
                  f.motto,
                  f.badge_icon,
                  COUNT(DISTINCT u.id) AS member_count,
                  COALESCE(SUM(r.points_awarded), 0) AS total_points,
                  COUNT(r.id) AS total_entries
           FROM factions f
           LEFT JOIN users u ON LOWER(TRIM(u.faction)) = LOWER(TRIM(f.name)) AND u.role = 'student' AND u.is_active = 1
           LEFT JOIN results r ON r.participant_id = u.id
           GROUP BY f.id, f.name, f.color, f.motto, f.badge_icon
           ORDER BY total_points DESC, member_count DESC, f.name ASC"""
    )


def create_faction(p):
    name = _text(p.get("name"), "Faction name", 80)
    color = _text(p.get("color", "#596fe0"), "Color", 30, False) or "#596fe0"
    motto = _text(p.get("motto", ""), "Motto", 255, False)
    badge = _text(p.get("badge_icon", "flag"), "Badge icon", 40, False) or "flag"
    return mutate(
        """INSERT INTO factions(name, color, motto, badge_icon) VALUES(%s, %s, %s, %s)""",
        (name, color, motto, badge),
    )


def update_faction(fid, p):
    fid = _integer(fid, "Faction ID")
    color = _text(p.get("color", "#596fe0"), "Color", 30, False) or "#596fe0"
    motto = _text(p.get("motto", ""), "Motto", 255, False)
    badge = _text(p.get("badge_icon", "flag"), "Badge icon", 40, False) or "flag"
    mutate(
        """UPDATE factions SET color=%s, motto=%s, badge_icon=%s WHERE id=%s""",
        (color, motto, badge, fid),
    )


def assign_student_faction(uid, faction_name):
    uid = _integer(uid, "Student ID")
    faction_name = _text(faction_name, "Faction name", 80)
    mutate(
        """UPDATE users SET faction=%s WHERE id=%s AND role='student'""",
        (faction_name, uid),
    )


def waiting_list(game_id=None, user_id=None):
    """Retrieve waiting list entries with student and game details."""
    init()
    sql = """SELECT w.id,
                    w.user_id,
                    w.game_id,
                    w.position,
                    w.status,
                    w.created_at,
                    u.display_name AS student_name,
                    u.username,
                    u.faction,
                    g.name AS game_name,
                    g.venue,
                    g.starts_at,
                    t.name AS tournament_name
             FROM waiting_lists w
             JOIN users u ON u.id = w.user_id
             JOIN games g ON g.id = w.game_id
             JOIN tournaments t ON t.id = g.tournament_id"""
    filters = []
    args = []
    if game_id is not None:
        filters.append("w.game_id = %s")
        args.append(int(game_id))
    if user_id is not None:
        filters.append("w.user_id = %s")
        args.append(int(user_id))
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY w.status ASC, w.position ASC, w.created_at ASC"
    return query(sql, tuple(args))


def join_waiting_list(user_id, game_id):
    """Enqueue a student onto an event's FIFO waiting list."""
    init()
    user_id = _integer(user_id, "Student ID")
    game_id = _integer(game_id, "Game ID")
    c = connect()
    try:
        cur = c.cursor(dictionary=True)
        # Check enrolled
        cur.execute("SELECT 1 FROM game_choices WHERE user_id=%s AND game_id=%s", (user_id, game_id))
        if cur.fetchone():
            raise ValueError("You are already enrolled in this game.")
        # Check already waiting
        cur.execute("SELECT id FROM waiting_lists WHERE user_id=%s AND game_id=%s AND status='waiting'", (user_id, game_id))
        if cur.fetchone():
            raise ValueError("You are already in the waiting list for this game.")
        # Compute position
        cur.execute("SELECT COALESCE(MAX(position), 0) + 1 AS next_pos FROM waiting_lists WHERE game_id=%s AND status='waiting'", (game_id,))
        next_pos = cur.fetchone()["next_pos"]
        cur.execute(
            """INSERT INTO waiting_lists(user_id, game_id, position, status) VALUES(%s, %s, %s, 'waiting')""",
            (user_id, game_id, next_pos),
        )
        wid = cur.lastrowid
        c.commit()
        return {"id": wid, "position": next_pos, "status": "waiting"}
    except:
        c.rollback()
        raise
    finally:
        c.close()


def withdraw_from_game(user_id, game_id):
    """
    Student withdraws from an event.
    Automatically dequeues the next eligible student from the FIFO waiting list and promotes them.
    """
    init()
    user_id = _integer(user_id, "Student ID")
    game_id = _integer(game_id, "Game ID")
    c = connect()
    try:
        cur = c.cursor(dictionary=True)
        cur.execute("SELECT 1 FROM game_choices WHERE user_id=%s AND game_id=%s FOR UPDATE", (user_id, game_id))
        if not cur.fetchone():
            raise ValueError("You are not currently enrolled in this game.")
        cur.execute("DELETE FROM game_choices WHERE user_id=%s AND game_id=%s", (user_id, game_id))

        # Check for waiting list student
        cur.execute(
            """SELECT w.id, w.user_id, u.display_name
               FROM waiting_lists w
               JOIN users u ON u.id = w.user_id
               WHERE w.game_id=%s AND w.status='waiting' AND u.is_active=1
               ORDER BY w.position ASC, w.created_at ASC
               LIMIT 1 FOR UPDATE""",
            (game_id,),
        )
        next_student = cur.fetchone()
        promoted = None
        if next_student:
            next_uid = next_student["user_id"]
            wid = next_student["id"]
            cur.execute("UPDATE waiting_lists SET status='promoted' WHERE id=%s", (wid,))
            cur.execute("INSERT INTO game_choices(user_id, game_id) VALUES(%s, %s)", (next_uid, game_id))
            promoted = {"user_id": next_uid, "name": next_student["display_name"]}

        c.commit()
        return {"withdrawn": True, "promoted": promoted}
    except:
        c.rollback()
        raise
    finally:
        c.close()


def enroll_single(user_id, game_id):
    """Enroll a student into a single game with full capacity and overlap validation."""
    init()
    user_id = _integer(user_id, "Student ID")
    game_id = _integer(game_id, "Game ID")
    c = connect()
    try:
        cur = c.cursor(dictionary=True)
        cur.execute("SELECT is_active FROM users WHERE id=%s FOR UPDATE", (user_id,))
        u = cur.fetchone()
        if not u or not u["is_active"]:
            raise ValueError("Student account not found or inactive.")

        # Check already enrolled
        cur.execute("SELECT 1 FROM game_choices WHERE user_id=%s AND game_id=%s", (user_id, game_id))
        if cur.fetchone():
            raise ValueError("You are already enrolled in this game.")

        # Check max 5 games
        cur.execute("SELECT COUNT(*) n FROM game_choices WHERE user_id=%s", (user_id,))
        if cur.fetchone()["n"] >= 5:
            raise ValueError("You can enroll in a maximum of 5 games across tournaments.")

        # Fetch candidate game
        cur.execute(
            """SELECT g.id, g.name, g.capacity, g.starts_at, g.duration_minutes, t.registration_closes_at
               FROM games g
               JOIN tournaments t ON t.id = g.tournament_id
               WHERE g.id=%s FOR UPDATE""",
            (game_id,),
        )
        game = cur.fetchone()
        if not game:
            raise ValueError("Game not found.")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        start = game["starts_at"] if isinstance(game["starts_at"], datetime) else datetime.fromisoformat(str(game["starts_at"]))
        closing = game["registration_closes_at"]
        if start <= now:
            raise ValueError("Registration is closed because this game has already started.")
        if closing and closing <= now:
            raise ValueError("Registration for this event has closed.")

        # Capacity check
        cur.execute("SELECT COUNT(*) n FROM game_choices WHERE game_id=%s", (game_id,))
        if cur.fetchone()["n"] >= game["capacity"]:
            raise ValueError("This game has reached full capacity. Join the waiting list instead!")

        # Check overlap with existing enrolled games
        new_end = start + timedelta(minutes=int(game["duration_minutes"]))
        cur.execute(
            """SELECT g.name, g.starts_at, g.duration_minutes
               FROM game_choices c
               JOIN games g ON g.id = c.game_id
               WHERE c.user_id=%s""",
            (user_id,),
        )
        for existing in cur.fetchall():
            ex_start = existing["starts_at"] if isinstance(existing["starts_at"], datetime) else datetime.fromisoformat(str(existing["starts_at"]))
            ex_end = ex_start + timedelta(minutes=int(existing["duration_minutes"]))
            if start < ex_end and ex_start < new_end:
                raise ValueError(f"This game conflicts with your enrolled game '{existing['name']}'.")

        cur.execute("INSERT INTO game_choices(user_id, game_id) VALUES(%s, %s)", (user_id, game_id))
        # If student was on waiting list, mark as promoted/resolved
        cur.execute("UPDATE waiting_lists SET status='promoted' WHERE user_id=%s AND game_id=%s AND status='waiting'", (user_id, game_id))
        c.commit()
        return {"enrolled": True, "game_id": game_id, "game_name": game["name"]}
    except:
        c.rollback()
        raise
    finally:
        c.close()


def matches(game_id=None, status=None):
    """Retrieve scheduled matches with real-time status and live scores."""
    init()
    sql = """SELECT m.id,
                    m.game_id,
                    m.round_number,
                    m.match_name,
                    m.venue,
                    m.starts_at,
                    m.status,
                    m.score1,
                    m.score2,
                    m.winner_id,
                    m.notes,
                    m.updated_at,
                    g.name AS game_name,
                    t.name AS tournament_name,
                    u1.id AS p1_id,
                    u1.display_name AS p1_name,
                    u1.faction AS p1_faction,
                    u2.id AS p2_id,
                    u2.display_name AS p2_name,
                    u2.faction AS p2_faction,
                    win.display_name AS winner_name
             FROM matches m
             JOIN games g ON g.id = m.game_id
             JOIN tournaments t ON t.id = g.tournament_id
             LEFT JOIN users u1 ON u1.id = m.participant1_id
             LEFT JOIN users u2 ON u2.id = m.participant2_id
             LEFT JOIN users win ON win.id = m.winner_id"""
    filters = []
    args = []
    if game_id is not None:
        filters.append("m.game_id = %s")
        args.append(int(game_id))
    if status is not None and str(status).lower() != "all":
        filters.append("m.status = %s")
        args.append(str(status).lower())
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY CASE m.status WHEN 'ongoing' THEN 1 WHEN 'upcoming' THEN 2 ELSE 3 END, m.starts_at ASC"
    return query(sql, tuple(args))


def create_match(p):
    """Create a new match or heat for a sport event."""
    game_id = _integer(p.get("game_id"), "Game ID")
    round_no = _integer(p.get("round_number", 1), "Round number", 1)
    match_name = _text(p.get("match_name"), "Match name", 160)
    venue = _text(p.get("venue", ""), "Venue", 160, False)
    starts_at = _date(p.get("starts_at"), "Match date and time")
    p1 = _integer(p.get("participant1_id"), "Participant 1", default=None)
    p2 = _integer(p.get("participant2_id"), "Participant 2", default=None)
    notes = _text(p.get("notes", ""), "Notes", 255, False)
    status = str(p.get("status", "upcoming")).lower()
    if status not in ("upcoming", "ongoing", "completed"):
        status = "upcoming"
    return mutate(
        """INSERT INTO matches(game_id, round_number, match_name, venue, starts_at, status, participant1_id, participant2_id, notes)
           VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (game_id, round_no, match_name, venue, starts_at, status, p1, p2, notes),
    )


def update_match(mid, p):
    """Update live score, status ('upcoming', 'ongoing', 'completed'), winner, and notes."""
    mid = _integer(mid, "Match ID")
    score1 = _integer(p.get("score1", 0), "Score 1", 0)
    score2 = _integer(p.get("score2", 0), "Score 2", 0)
    status = str(p.get("status", "ongoing")).lower()
    if status not in ("upcoming", "ongoing", "completed"):
        status = "ongoing"
    winner_id = p.get("winner_id")
    winner_id = _integer(winner_id, "Winner ID") if winner_id not in (None, "") else None
    notes = _text(p.get("notes", ""), "Notes", 255, False)
    mutate(
        """UPDATE matches
           SET score1=%s, score2=%s, status=%s, winner_id=%s, notes=%s
           WHERE id=%s""",
        (score1, score2, status, winner_id, notes, mid),
    )


def announcements():
    """Retrieve all tournament announcements."""
    init()
    return query(
        """SELECT a.id,
                  a.title,
                  a.content,
                  a.category,
                  a.is_pinned,
                  a.created_at,
                  COALESCE(u.display_name, 'Organizing Committee') AS author
           FROM announcements a
           LEFT JOIN users u ON u.id = a.author_id
           ORDER BY a.is_pinned DESC, a.created_at DESC"""
    )


def create_announcement(p, author_id=None):
    """Publish a new announcement for students."""
    title = _text(p.get("title"), "Title", 160)
    content = _text(p.get("content"), "Content", 4000)
    category = _text(p.get("category", "General"), "Category", 60, False) or "General"
    pinned = 1 if p.get("is_pinned") else 0
    return mutate(
        """INSERT INTO announcements(title, content, category, author_id, is_pinned)
           VALUES(%s, %s, %s, %s, %s)""",
        (title, content, category, author_id, pinned),
    )

