# Python + SQL: injection and missing-row crash

## Request (input)

> Find bugs in `find_user`.

## Bug Hunter report (output)

| # | Location | Status | Severity | Finding |
|---|---|---|---|---|
| 1 | [buggy.py](buggy.py) line 7 | Confirmed | Critical if `username` is user-controlled | SQL injection: `username` is formatted into the SQL text. The payload `nobody' OR '1'='1` returns a real user's row. |
| 2 | [buggy.py](buggy.py) line 9 | Confirmed | Medium | When no row matches, `fetchone()` returns `None` and `row[0]` raises `TypeError`. |

**Evidence:** reproduced against an in-memory SQLite database by `test_buggy_version_is_injectable` and `test_buggy_version_crashes_on_missing_user` in [test_example.py](test_example.py).

**Fix** ([fixed.py](fixed.py)):

```diff
-    cur = conn.execute(f"SELECT id, name FROM users WHERE name = '{username}'")
+    cur = conn.execute("SELECT id, name FROM users WHERE name = ?", (username,))
     row = cur.fetchone()
+    if row is None:
+        return None
     return {"id": row[0], "name": row[1]}
```

**Regression review:** existing users are still found, and names containing quotes now work (they broke the old query). The function now returns `None` for unknown users instead of raising `TypeError`. Callers must handle `None`. This is an interface change, so the callers need to be reviewed.

**Not verified:** the callers were not provided, so whether `username` comes from user input is an assumption.

**Tests:** `python examples/python-sql-injection/test_example.py`
