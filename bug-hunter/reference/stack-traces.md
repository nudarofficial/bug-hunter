# Reading Stack Traces and Logs

## Contents
- General method
- Reading order by language
- Common exception meanings
- Logs and error messages
- When the trace is misleading

## General method

1. Find the **exception type and message** first. Copy them exactly; do not paraphrase when reporting.
2. Find the **deepest frame in project code**. Library frames usually show *where* it failed, not *why*.
3. Find the **first frame where state was already wrong**. Walk up the stack and ask, for each frame, "was the bad value created here or passed in?"
4. Look for **chained causes** (`Caused by:`, `During handling of the above exception`, `The above exception was the direct cause`, wrapped Go errors). The root cause is usually the innermost one.
5. Note **line numbers against the right version** of the file. If the trace came from a deployed build, the local file may differ.

## Reading order by language

| Language | Most recent call | Chained cause marker |
|---|---|---|
| Python | **Last** line of the traceback | `The above exception was the direct cause of...` / `During handling of the above exception...` |
| Java / Kotlin | **First** `at` line | `Caused by:` (read the last one first) |
| C# / .NET | **First** `at` line | `---> ` inner exception, `--- End of inner exception stack trace ---` |
| JavaScript / Node.js | **First** `at` line | `[cause]:` (Error `cause` property) |
| Go (panic) | First `goroutine N [running]:` block, top frame | Wrapped errors: `fmt.Errorf("...: %w", err)` text reads outer → inner |
| Rust (panic) | `RUST_BACKTRACE=1` output; frames after `rust_begin_unwind`/`core::panicking` | `Caused by:` in `anyhow`/`eyre` reports |
| PHP | `#0` is the most recent frame | `Next` exception blocks |
| Ruby | **First** line is where it was raised | `cause` shown after the main backtrace |
| C / C++ | Debugger/ASan: frame `#0` is most recent | Sanitizer reports include "previously allocated/freed by" sections |

## Common exception meanings

| Message | Usual root causes to check |
|---|---|
| Python `KeyError`, `IndexError` | Missing key from external data; off-by-one; empty collection not handled upstream |
| Python `AttributeError: 'NoneType' object has no attribute` | A function returned `None` on a path the caller did not expect (miss, early return, in-place method like `list.sort()`) |
| Python `UnboundLocalError` | Assignment later in the function makes a name local; missing `global`/`nonlocal` |
| JS `TypeError: Cannot read properties of undefined` | Missing `await`; wrong property name; optional API field; array index past end |
| JS `UnhandledPromiseRejection` | A promise created without `await`/`.catch`; `forEach` with an `async` callback |
| Java `NullPointerException` | Unchecked map lookup; uninitialized field; auto-unboxing a `null` `Integer` |
| Java `ConcurrentModificationException` | Modifying a collection while iterating it (same thread too) |
| C# `NullReferenceException` | Same as Java NPE; also nullable context disabled |
| C# `InvalidOperationException: Collection was modified` | Same as Java CME |
| Go `panic: assignment to entry in nil map` | Map declared but not `make`d |
| Go `panic: runtime error: invalid memory address or nil pointer dereference` | Ignored `err`, using the zero-value result; nil interface vs typed nil |
| Go `fatal error: all goroutines are asleep - deadlock!` | Unbuffered channel send with no receiver; `WaitGroup` count mismatch |
| Rust `called Option::unwrap() on a None value` | `unwrap` on fallible input; replace with explicit handling at the right layer |
| Rust `already borrowed: BorrowMutError` | Overlapping `RefCell` borrows across a call |
| C/C++ `Segmentation fault` | Null/dangling pointer, out-of-bounds, use-after-free, stack overflow. Re-run with AddressSanitizer (`-fsanitize=address -g`) when possible |
| SQL `deadlock detected` | Two transactions lock rows in different orders |
| SQL `duplicate key value violates unique constraint` | Check-then-insert race; missing upsert |

## Logs and error messages

- Line up events by **timestamp and request/trace ID**, not by line order — logs from concurrent workers interleave.
- The **first** error in a burst is usually the cause; later ones are fallout (connection pool exhausted, timeouts, retries).
- Watch for **swallowed errors**: `except: pass`, empty `catch {}`, `_ = err`, `.catch(() => {})`. They make the visible failure appear far from the cause.
- Distinguish **timeouts** (slow dependency, lock contention, missing index) from **connection refused** (service down, wrong host/port) from **connection reset** (peer crash, proxy limits, TLS mismatch).

## When the trace is misleading

- **Async code**: JavaScript and Python async traces may omit the scheduling caller. Look for the `await` that was missing or the task that was never awaited.
- **Minified / transpiled code**: Map through source maps before drawing conclusions.
- **Optimized native builds**: Inlined frames and wrong line numbers are common; rebuild with debug info (`-O0 -g`) if allowed.
- **Re-thrown exceptions**: `raise e` / `throw e` may reset the trace origin in some languages (C# `throw ex;` loses it; `throw;` keeps it).
- **Error raised far from the defect**: A corrupt value written early (bad cache entry, bad DB row) may only explode later. Trace the value's origin, not just the crash site.
