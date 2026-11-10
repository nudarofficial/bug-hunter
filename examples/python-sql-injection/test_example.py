"""Regression tests for the SQL injection and missing-row bugs.

Uses an in-memory SQLite database only; no external system is touched.
"""

import importlib.util
import pathlib
import sqlite3
import unittest

HERE = pathlib.Path(__file__).resolve().parent
PAYLOAD = "nobody' OR '1'='1"


def load(name):
    spec = importlib.util.spec_from_file_location(f"sqli_{name}", HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    conn.executemany("INSERT INTO users (name) VALUES (?)", [("alice",), ("bob",)])
    return conn


class SqlInjectionTest(unittest.TestCase):
    def setUp(self):
        self.conn = make_db()

    def tearDown(self):
        self.conn.close()

    def test_buggy_version_is_injectable(self):
        buggy = load("buggy")
        # The payload matches no real user, yet the query returns the first row.
        self.assertEqual(buggy.find_user(self.conn, PAYLOAD)["name"], "alice")

    def test_buggy_version_crashes_on_missing_user(self):
        buggy = load("buggy")
        with self.assertRaises(TypeError):
            buggy.find_user(self.conn, "carol")

    def test_fixed_version_treats_payload_as_data(self):
        fixed = load("fixed")
        self.assertIsNone(fixed.find_user(self.conn, PAYLOAD))

    def test_fixed_version_finds_existing_user(self):
        fixed = load("fixed")
        self.assertEqual(fixed.find_user(self.conn, "bob"), {"id": 2, "name": "bob"})

    def test_fixed_version_handles_quotes_in_names(self):
        fixed = load("fixed")
        self.conn.execute("INSERT INTO users (name) VALUES (?)", ("o'brien",))
        self.assertEqual(fixed.find_user(self.conn, "o'brien")["name"], "o'brien")


if __name__ == "__main__":
    unittest.main()
