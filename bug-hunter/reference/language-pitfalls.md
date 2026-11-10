# Language-Specific Bug Patterns

Check these when the symptom matches. Each item names the trap and the usual fix. Version-dependent behavior is called out; confirm the project's version before reporting.

## Contents
- Python
- JavaScript
- TypeScript
- Java
- C
- C++
- C#
- Go
- Rust
- PHP
- Ruby
- SQL

## Python

- **Mutable default arguments** (`def f(x, acc=[])`) are shared across calls. Use `None` and create inside.
- **Late-binding closures** in loops: `lambda: i` captures the variable, not the value. Bind with a default arg or `functools.partial`.
- **`is` vs `==`** for strings/ints works by accident for small cached values only.
- **In-place methods return `None`**: `x = x.sort()`, `x = x.append(...)`.
- **Modifying a list/dict while iterating** skips items or raises `RuntimeError`.
- **Integer vs float division**: `/` always returns float in Python 3; `//` floors toward negative infinity (`-7 // 2 == -4`).
- **Float money math**: use `decimal.Decimal` or integer cents.
- **Naive vs aware `datetime`** comparisons raise `TypeError`; mixing local time and UTC gives silent offsets.
- **Broad `except Exception:` / bare `except:`** hides the real error, and bare `except` also catches `KeyboardInterrupt`/`SystemExit`.
- **asyncio**: calling a coroutine without `await` does nothing (`RuntimeWarning: coroutine was never awaited`); blocking calls (`time.sleep`, sync I/O) inside `async def` stall the loop.
- **Shallow copies**: `list(x)`, `dict.copy()`, `[[0]*n]*m` share inner objects.

## JavaScript

- **`async` callbacks in `forEach`/`map`** are not awaited. Use `for...of` with `await` or `await Promise.all(arr.map(...))`.
- **Missing `await`** yields a pending `Promise` where a value was expected; truthy checks on a Promise always pass.
- **`==` coercion**: `0 == ''`, `null == undefined`, `'1' == 1`. Prefer `===`.
- **`this` binding** lost when passing methods as callbacks. Use arrow functions or `.bind`.
- **Floating point**: `0.1 + 0.2 !== 0.3`. Use integer cents or a decimal library for money.
- **`parseInt` without radix** on legacy engines; `parseInt('08')`. Also `Number('')` is `0`.
- **Array `sort()` default is lexicographic**: `[10, 9, 1].sort()` → `[1, 10, 9]`. Pass a comparator.
- **Mutating shared objects** (default params are fresh per call in JS, but module-level objects are shared across requests in servers).
- **`Date` months are 0-based**; `new Date('2024-01-01')` is UTC, `new Date(2024, 0, 1)` is local time.
- **Event listeners / intervals not removed** cause leaks and duplicate handlers.

## TypeScript

All JavaScript pitfalls apply at runtime; types are erased.

- **`as` casts and `!` non-null assertions** silence the compiler without checking anything at runtime.
- **`any` leaking from untyped JSON** (`JSON.parse`, `fetch().json()`) — validate external data at the boundary.
- **Optional properties vs `undefined`**: with `exactOptionalPropertyTypes` off, `{a?: string}` accepts `{a: undefined}`.
- **Index signatures** return `T`, not `T | undefined`, unless `noUncheckedIndexedAccess` is enabled.
- **Enums**: numeric enums accept any number; string unions are usually safer.

## Java

- **`==` on objects** (including `Integer` outside -128..127 and `String`) compares references. Use `.equals`.
- **Auto-unboxing `null`** throws `NullPointerException` (`int x = map.get(k);`).
- **`equals` without `hashCode`** breaks `HashMap`/`HashSet`.
- **`ConcurrentModificationException`** when removing during for-each; use `Iterator.remove` or `removeIf`.
- **`SimpleDateFormat` is not thread-safe**; use `java.time`.
- **Integer overflow** is silent; use `Math.addExact` or `long`.
- **Resources not closed** — use try-with-resources.
- **`Optional.get()`** without a presence check.

## C

- **Buffer overflows**: `strcpy`, `strcat`, `sprintf`, `gets`, unchecked `memcpy` lengths. Use bounded variants and check lengths.
- **Off-by-one** with `'\0'` terminators (`malloc(strlen(s))` instead of `+ 1`).
- **Use-after-free / double free**; set pointers to `NULL` after `free` where ownership is unclear.
- **Uninitialized variables** and unchecked `malloc` returns.
- **Signed/unsigned comparison** and integer overflow (signed overflow is undefined behavior).
- **Format string bugs**: `printf(user_input)`.
- Verify with `-Wall -Wextra`, AddressSanitizer, UndefinedBehaviorSanitizer, or Valgrind when available.

## C++

- C pitfalls above, plus:
- **Iterator invalidation** after `push_back`, `erase`, `insert`.
- **Dangling references** to temporaries, to elements of resized vectors, or captured by reference in lambdas that outlive the scope.
- **Missing virtual destructor** in polymorphic base classes.
- **Rule of 3/5/0** violations with raw owning pointers; prefer `std::unique_ptr`.
- **Data races** on non-atomic shared state; verify with ThreadSanitizer.

## C#

- **`async void`** methods swallow exceptions into the synchronization context; use `async Task` except for event handlers.
- **`.Result` / `.Wait()`** on tasks can deadlock under a synchronization context.
- **`IDisposable` not disposed** — use `using`.
- **LINQ deferred execution**: enumerating a query twice re-runs it; modifying the source between enumerations changes results.
- **`throw ex;`** resets the stack trace; use `throw;`.
- **Closures over loop variables** in `for` loops (not `foreach` since C# 5).

## Go

- **Ignored errors** (`v, _ := f()`) followed by use of the zero value.
- **Nil map writes** panic; `make` the map first.
- **Loop variable capture** in goroutines/closures before Go 1.22 shares one variable across iterations; Go 1.22+ creates one per iteration. Check `go.mod`.
- **Typed nil in interface**: returning a nil `*MyErr` as `error` is non-nil.
- **Goroutine leaks** from channels nobody reads; missing `context` cancellation.
- **`defer` in loops** runs at function exit, not iteration end (file handle exhaustion).
- **Slices sharing backing arrays** after `append` on a sub-slice.
- **Data races** — verify with `go test -race`.

## Rust

- **`unwrap`/`expect` on fallible input** panics in production; propagate with `?`.
- **Integer overflow** panics in debug, wraps in release. Use `checked_*`/`saturating_*` where it matters.
- **`RefCell` double borrow** at runtime; **`Mutex` poisoning** after a panic.
- **Blocking in async** (`std::thread::sleep`, sync I/O in a Tokio task).
- **`unsafe` blocks** — check aliasing, lifetimes, and bounds by hand; run Miri if available.
- **Slicing strings by byte index** panics on non-ASCII boundaries.

## PHP

- **Loose comparison `==`**: `"abc" == 0` is `true` before PHP 8 and `false` from PHP 8. `"1e3" == "1000"` is `true`. Use `===`.
- **`strpos` returning `0`** treated as false; compare `!== false`.
- **SQL injection** via string interpolation; use PDO prepared statements.
- **Unescaped output** causes XSS; use `htmlspecialchars` with `ENT_QUOTES` and the correct charset.
- **References in `foreach`** (`foreach ($a as &$v)`) persist after the loop; `unset($v)`.
- **`array_merge` reindexes numeric keys**; `+` keeps the left keys.

## Ruby

- **`nil` from failed lookups** (`hash[:missing]`) — use `fetch` to fail loudly.
- **Mutable string/array constants** shared across calls; freeze them.
- **`==` vs `equal?` vs `eql?`** in hash keys.
- **N+1 queries** in ActiveRecord; use `includes`/`preload`.
- **`rescue => e`** catches `StandardError` only; bare `rescue Exception` also catches interrupts.
- **Mass assignment** without strong parameters.

## SQL

- **`NOT IN` with a subquery that returns `NULL`** yields no rows. Use `NOT EXISTS`.
- **`= NULL`** is never true; use `IS NULL`.
- **Implicit type conversion** defeats indexes and can match unexpected rows (MySQL `'abc' = 0` in older modes).
- **`LEFT JOIN` turned into `INNER JOIN`** by a `WHERE` filter on the right table; move the filter into `ON`.
- **Aggregates with `NULL`**: `COUNT(col)` skips nulls, `COUNT(*)` does not; `AVG` ignores nulls.
- **Missing `ORDER BY`** — row order is undefined without it, including with `LIMIT`.
- **Race conditions** in read-then-write; use transactions with the right isolation level, `SELECT ... FOR UPDATE`, or atomic upserts.
- **String-built queries** — use bound parameters.
