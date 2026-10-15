import unittest
from unittest.mock import patch

import database


class FakeCursor:
    def __init__(self, exists=True, result_count=0, game_ids=()):
        self.fetchone_values = [
            (1,) if exists else None,
            (result_count,),
        ]
        self.game_ids = [(game_id,) for game_id in game_ids]
        self.statements = []

    def execute(self, sql, params=None):
        self.statements.append((" ".join(sql.split()).upper(), params))

    def fetchone(self):
        return self.fetchone_values.pop(0)

    def fetchall(self):
        return self.game_ids


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class TournamentDeletionTests(unittest.TestCase):
    def run_delete(self, cursor):
        connection = FakeConnection(cursor)
        with (
            patch.object(database, "init"),
            patch.object(database, "connect", return_value=connection),
        ):
            database.delete_tournament(42)
        return connection

    def test_deletes_tournament_and_all_related_rows_atomically(self):
        cursor = FakeCursor(game_ids=(8, 9))

        connection = self.run_delete(cursor)

        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        self.assertTrue(connection.closed)
        deleted_tables = [
            sql.split(" FROM ", 1)[1].split(" WHERE ", 1)[0]
            for sql, _ in cursor.statements
            if sql.startswith("DELETE ")
        ]
        self.assertEqual(
            deleted_tables,
            ["RESULTS", "GAME_CHOICES", "GAMES", "TOURNAMENTS"],
        )

    def test_deletes_tournament_with_no_games(self):
        cursor = FakeCursor(game_ids=())

        connection = self.run_delete(cursor)

        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        deleted_tables = [
            sql.split(" FROM ", 1)[1].split(" WHERE ", 1)[0]
            for sql, _ in cursor.statements
            if sql.startswith("DELETE ")
        ]
        self.assertEqual(deleted_tables, ["TOURNAMENTS"])

    def test_refuses_to_delete_tournament_with_published_results(self):
        cursor = FakeCursor(result_count=1)
        connection = FakeConnection(cursor)

        with (
            patch.object(database, "init"),
            patch.object(database, "connect", return_value=connection),
            self.assertRaisesRegex(ValueError, "published results"),
        ):
            database.delete_tournament(42)

        self.assertFalse(connection.committed)
        self.assertTrue(connection.rolled_back)
        self.assertTrue(connection.closed)
        self.assertFalse(any(sql.startswith("DELETE ") for sql, _ in cursor.statements))

    def test_missing_tournament_rolls_back_without_deleting(self):
        cursor = FakeCursor(exists=False)
        connection = FakeConnection(cursor)

        with (
            patch.object(database, "init"),
            patch.object(database, "connect", return_value=connection),
            self.assertRaisesRegex(ValueError, "no longer exists"),
        ):
            database.delete_tournament(42)

        self.assertFalse(connection.committed)
        self.assertTrue(connection.rolled_back)
        self.assertTrue(connection.closed)
        self.assertFalse(any(sql.startswith("DELETE ") for sql, _ in cursor.statements))


if __name__ == "__main__":
    unittest.main()
