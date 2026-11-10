"""Fixed version: bound parameter and explicit handling of a missing user."""


def find_user(conn, username):
    cur = conn.execute("SELECT id, name FROM users WHERE name = ?", (username,))
    row = cur.fetchone()
    if row is None:
        return None
    return {"id": row[0], "name": row[1]}
