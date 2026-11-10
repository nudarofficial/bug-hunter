"""Buggy version: user lookup built with string formatting."""


def find_user(conn, username):
    # BUG: username is interpolated into the SQL text (SQL injection),
    # and a missing user crashes with TypeError on row[0].
    cur = conn.execute(f"SELECT id, name FROM users WHERE name = '{username}'")
    row = cur.fetchone()
    return {"id": row[0], "name": row[1]}
