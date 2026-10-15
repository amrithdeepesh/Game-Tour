import os
import unittest
from datetime import datetime
from unittest.mock import patch

import database
import app


class InputValidationTests(unittest.TestCase):
    def test_scoring_rules_accept_descending_points(self):
        self.assertEqual(
            database._rules(
                {
                    "points_first": 12,
                    "points_second": 8,
                    "points_third": 4,
                    "points_participation": 0,
                }
            ),
            [12, 8, 4, 0],
        )

    def test_whole_number_fields_reject_fractional_values(self):
        with self.assertRaises(ValueError):
            database._integer(2.5, "Rounds")
        with self.assertRaises(ValueError):
            database._integer("1.2", "Score")

    def test_scoring_rules_reject_increasing_or_negative_points(self):
        with self.assertRaises(ValueError):
            database._rules(
                {
                    "points_first": 5,
                    "points_second": 8,
                    "points_third": 3,
                    "points_participation": 1,
                }
            )
        with self.assertRaises(ValueError):
            database._rules(
                {
                    "points_first": 10,
                    "points_second": 7,
                    "points_third": 5,
                    "points_participation": -1,
                }
            )

    def test_datetime_offsets_are_normalized_to_utc(self):
        value = database._date("2026-10-12T10:30:00+05:30", "date")
        self.assertEqual(value, datetime(2026, 10, 12, 5, 0))

    def test_game_capacity_round_and_duration_limits(self):
        payload = {
            "name": "Chess",
            "venue": "Hall A",
            "tournament_id": 1,
            "starts_at": "2026-10-12 10:00:00",
            "capacity": 12,
            "rounds": 2,
            "duration_minutes": 45,
        }
        self.assertEqual(database._game_values(payload)[-1], 12)
        for key, value in (("capacity", 0), ("rounds", 21), ("duration_minutes", 4)):
            with self.subTest(key=key):
                invalid = dict(payload, **{key: value})
                with self.assertRaises(ValueError):
                    database._game_values(invalid)

    def test_form_text_rejects_control_characters_and_oversize(self):
        with self.assertRaises(ValueError):
            database._text("bad\nname", "Name", 20)
        with self.assertRaises(ValueError):
            database._text("x" * 21, "Name", 20)

    def test_mutations_allow_local_frontend_on_supported_dev_ports(self):
        with patch.dict(os.environ, {"FRONTEND_ORIGINS": ""}, clear=False):
            for origin in (
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ):
                with self.subTest(origin=origin):
                    self.assertTrue(app._allowed_frontend_origin(origin))

    def test_mutations_reject_untrusted_browser_origins(self):
        with patch.dict(os.environ, {"FRONTEND_ORIGINS": ""}, clear=False):
            for origin in (
                "https://localhost:3000",
                "http://localhost:3002",
                "http://attacker.example:3001",
                "https://attacker.example",
            ):
                with self.subTest(origin=origin):
                    self.assertFalse(app._allowed_frontend_origin(origin))

    def test_password_hash_is_salted_and_verifiable(self):
        first = app.password_hash("correct horse battery staple")
        second = app.password_hash("correct horse battery staple")
        self.assertNotEqual(first, second)
        self.assertTrue(app.password_ok("correct horse battery staple", first))
        self.assertFalse(app.password_ok("incorrect password", first))


if __name__ == "__main__":
    unittest.main()
