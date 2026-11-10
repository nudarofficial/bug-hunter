# Worked Examples

Each example shows the input a user might give and the shape of a good response. Error text inside a **User** block is part of the scenario (what the user pasted). The responses show the expected level of evidence, status labelling, and fix size.

## Contents
- Python: state leaking between calls
- JavaScript: async callback in forEach
- TypeScript: non-null assertion hides a miss
- Java: boxed Integer comparison
- Go: nil map write, plus a version-dependent risk
- C: missing byte for the terminator
- C++: reference invalidated by push_back
- C#: exception lost in async void
- Rust: slicing a string by byte index
- PHP: strpos returning 0
- Ruby: nil from a missing hash key
- SQL: NOT IN with NULL
- Code review with mixed findings

---

## Python: state leaking between calls

**User:** "Each call to `add_tag` returns tags from earlier posts."

```python
def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags
```

**Response:**
- **Root cause (Confirmed, deterministic code path):** the default list is created once at function definition and shared by every call that omits `tags`.
- **Fix:**
  ```python
  def add_tag(tag, tags=None):
      if tags is None:
          tags = []
      tags.append(tag)
      return tags
  ```
- **Regression check:** callers that pass their own list still get it mutated in place, as before.
- **Test:** `assert add_tag("a") == ["a"]; assert add_tag("b") == ["b"]`.

A runnable version is in the repository under `examples/python-mutable-default/`.

---

## JavaScript: async callback in forEach

**User:** "`total` is always 0."

```js
async function totalPrice(ids) {
  let total = 0;
  ids.forEach(async (id) => {
    const item = await fetchItem(id);
    total += item.price;
  });
  return total;
}
```

**Response:**
- **Root cause (Confirmed):** `forEach` ignores the promises returned by the async callback, so `return total` runs before any `await` resolves.
- **Fix:** `const items = await Promise.all(ids.map(fetchItem)); return items.reduce((s, i) => s + i.price, 0);`
- **Trade-off:** `Promise.all` runs requests concurrently. If the API is rate-limited, use a `for...of` loop with `await` instead.
- **Potential risk:** prices as floats can accumulate rounding error; integer cents avoid it. Reported separately, not changed.

---

## TypeScript: non-null assertion hides a miss

**User:** "`TypeError: Cannot read properties of undefined (reading 'email')` in `notify`."

```ts
const user = users.find(u => u.id === order.userId)!;
send(user.email);
```

**Response:**
- **Root cause (Confirmed by the trace and code):** `find` returns `undefined` when no user matches; `!` removes the compile-time check but adds no runtime check.
- **Needs verification:** why the user is missing (deleted account? wrong ID type, e.g. `"42"` vs `42`?). Check the type of `order.userId` at runtime.
- **Fix:** handle the miss explicitly at this layer (log and skip, or throw a domain error) instead of asserting.

---

## Java: boxed Integer comparison

**User:** "Orders with quantity above 127 are never matched."

```java
Integer expected = order.getQuantity();
Integer actual = shipment.getQuantity();
if (expected == actual) { markShipped(order); }
```

**Response:**
- **Root cause (Confirmed):** `==` on `Integer` compares references. Values from -128 to 127 are cached by `Integer.valueOf` by default, so small values happen to compare equal; larger values do not.
- **Fix:** `if (Objects.equals(expected, actual))` — also handles `null` without throwing.

---

## Go: nil map write, plus a version-dependent risk

**User:** "`panic: assignment to entry in nil map`"

```go
type Index struct{ byName map[string]int }

func (ix *Index) Add(name string, id int) { ix.byName[name] = id }

func Build(names []string) *Index {
    ix := &Index{}
    for i, n := range names {
        go func() { ix.Add(n, i) }()
    }
    return ix
}
```

**Response:**
- **Finding 1 — Confirmed, High:** `byName` is never initialized. Fix: `ix := &Index{byName: make(map[string]int)}`.
- **Finding 2 — Confirmed, High:** concurrent writes to a map from multiple goroutines without synchronization is a data race (`go test -race` would report it; Go may also abort with `concurrent map writes`). Fix: add the entries synchronously, or guard with a `sync.Mutex` and wait with a `sync.WaitGroup`.
- **Finding 3 — Potential risk (depends on Go version):** before Go 1.22, the closures share `n` and `i`. Check the `go` directive in `go.mod`. Removing the goroutines also removes this risk.
- **Also:** `Build` returns before the goroutines finish, so the index may be incomplete. Synchronous insertion is the minimal fix for all three.

---

## C: missing byte for the terminator

```c
char *dup(const char *s) {
    char *p = malloc(strlen(s));
    strcpy(p, s);
    return p;
}
```

**Response:**
- **Root cause (Confirmed by code path):** `strlen` excludes the `'\0'`; `strcpy` writes `strlen(s) + 1` bytes, overflowing the heap buffer by one. Also `malloc` is unchecked.
- **Fix:**
  ```c
  char *dup(const char *s) {
      size_t n = strlen(s) + 1;
      char *p = malloc(n);
      if (p == NULL) return NULL;
      memcpy(p, s, n);
      return p;
  }
  ```
- **How to confirm at runtime:** build with `-fsanitize=address -g` and call `dup("abc")`; ASan reports a heap-buffer-overflow. (Not executed here.)

---

## C++: reference invalidated by push_back

```cpp
std::vector<Task> tasks = load();
Task& first = tasks[0];
tasks.push_back(makeFollowUp(first));
log(first.name);   // crash or garbage
```

**Response:**
- **Root cause (Confirmed):** `push_back` may reallocate, invalidating `first`. Using it afterwards is undefined behavior.
- **Fix:** copy what you need before the push (`std::string name = tasks[0].name;`), or index again after it (`tasks[0].name`). Also check `tasks` is non-empty before `tasks[0]`.

---

## C#: exception lost in async void

```csharp
public async void SaveAsync(Order o) {
    await _repo.InsertAsync(o);
}
// caller
try { SaveAsync(order); } catch (Exception ex) { _log.Error(ex); }
```

**Response:**
- **Root cause (Confirmed):** an `async void` method cannot be awaited, so the caller's `try/catch` never sees the exception; it is raised on the synchronization context and may crash the process.
- **Fix:** change to `public async Task SaveAsync(Order o)` and `await SaveAsync(order);` in the caller. Every caller must be updated — list them.

---

## Rust: slicing a string by byte index

**User:** "Panics with `byte index 10 is not a char boundary` for some names."

```rust
fn preview(s: &str) -> &str { if s.len() > 10 { &s[..10] } else { s } }
```

**Response:**
- **Root cause (Confirmed):** `len()` and slicing use bytes; multi-byte UTF-8 characters can straddle byte 10.
- **Fix (keeps the borrowed return type):**
  ```rust
  fn preview(s: &str) -> &str {
      match s.char_indices().nth(10) {
          Some((idx, _)) => &s[..idx],
          None => s,
      }
  }
  ```
- **Behavior change to note:** the limit is now 10 characters (Unicode scalar values) instead of 10 bytes. Confirm that is the intent.

---

## PHP: strpos returning 0

```php
if (strpos($path, '/admin')) { requireAdmin(); }
```

**Response:**
- **Root cause (Confirmed, Critical if `$path` is the request path):** `strpos` returns `0` when the match is at the start, which is falsy, so `/admin/...` skips the check.
- **Fix:** `if (str_starts_with($path, '/admin'))` on PHP 8+, or `strpos($path, '/admin') === 0`.
- **Needs verification:** whether other routes rely on this check; a prefix match also covers `/administrator`.

---

## Ruby: nil from a missing hash key

**User:** "`undefined method 'upcase' for nil` in `format_country`."

```ruby
def format_country(address)
  address[:country].upcase
end
```

**Response:**
- **Root cause (Confirmed by trace):** `Hash#[]` returns `nil` for a missing key. Some addresses have no `:country`.
- **Needs verification:** whether missing country is valid data. If valid: `address.fetch(:country, "").upcase` or a safe-navigation default. If invalid: `address.fetch(:country)` to fail loudly at the boundary, and fix the producer.

---

## SQL: NOT IN with NULL

**User:** "This returns zero rows even though some customers never ordered."

```sql
SELECT id FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders);
```

**Response:**
- **Root cause (Confirmed if any `orders.customer_id` is NULL):** `x NOT IN (..., NULL)` evaluates to UNKNOWN, never TRUE, so no rows qualify.
- **Verify with:** `SELECT COUNT(*) FROM orders WHERE customer_id IS NULL;`
- **Fix:**
  ```sql
  SELECT c.id FROM customers c
  WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);
  ```

---

## Code review with mixed findings

**User:** "Find bugs in this function."

```python
def get_user(conn, username):
    cur = conn.execute(f"SELECT * FROM users WHERE name = '{username}'")
    row = cur.fetchone()
    return {"id": row[0], "name": row[1]}
```

**Response:**

| # | Location | Status | Severity | Finding |
|---|---|---|---|---|
| 1 | line 2 | Confirmed | Critical if `username` is user-controlled | SQL injection via f-string. Fix: `conn.execute("SELECT * FROM users WHERE name = ?", (username,))` |
| 2 | line 4 | Confirmed | Medium | `fetchone()` returns `None` for unknown users → `TypeError`. Return `None` or raise a domain error. |
| 3 | line 2 | Potential risk | Low | `SELECT *` with positional access breaks if column order changes. Select columns explicitly. |

**Not verified:** callers were not shown, so whether `username` reaches this function from user input is assumed. A runnable version of finding 1 is in `examples/python-sql-injection/`.
