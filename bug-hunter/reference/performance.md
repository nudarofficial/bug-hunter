# Performance Defect Investigation

**Measure before claiming.** A performance finding is Confirmed only with a measurement (profiler output, timing, query plan, metrics) or an unambiguous complexity argument on realistic input sizes. Never report a speedup figure you did not measure; say "expected to reduce X from O(n²) to O(n)" instead.

## Workflow

1. **Quantify the symptom**: which operation, how slow, on what input size, since when, how often.
2. **Profile or time it** with the project's tools when execution is allowed:
   - Python: `python -m cProfile -s cumtime script.py`, `py-spy`
   - Node.js: `node --prof`, `node --cpu-prof`, Chrome DevTools
   - Java: JFR, async-profiler
   - Go: `go test -bench . -cpuprofile cpu.out`, `pprof`
   - Rust: `cargo bench`, `perf`, `cargo flamegraph`
   - .NET: `dotnet-trace`, `dotnet-counters`
   - SQL: `EXPLAIN` / `EXPLAIN ANALYZE` (PostgreSQL), `EXPLAIN` (MySQL), actual execution plan (SQL Server)
3. **Locate the hot spot** in the profile, then read that code.
4. **Fix the dominant cost first.** Micro-optimizations elsewhere are out of scope unless asked.
5. **Re-measure with the same method** and report before/after numbers with the command used.

## Common causes

| Pattern | Signal | Fix |
|---|---|---|
| N+1 queries | Query count grows with result rows | Join, batch load, ORM eager loading |
| Missing index | Sequential scan on a large table in the plan | Add an index matching the filter/sort; confirm with the plan |
| Function on indexed column | `WHERE LOWER(email) = ...` ignores the index | Expression index or normalized column |
| Quadratic loops | `x in list` inside a loop; nested scans | Use a set/dict/hash map |
| Repeated string concatenation in loops | Time grows superlinearly | Join once / use a builder |
| Unbounded caches or listeners | Memory grows with uptime | Size limit, TTL, weak references, remove listeners |
| Blocking I/O on event loop | Latency spikes for all requests | Async I/O or offload to a worker |
| Sequential awaits that could be concurrent | Total time = sum of calls | `Promise.all`, `asyncio.gather`, `errgroup` — only if calls are independent |
| Lock contention | CPU low, latency high | Narrow critical sections, shard state |
| Excessive allocation | GC time high | Reuse buffers, avoid intermediate collections |
| Chatty network calls | Many small requests | Batch endpoints, pagination size |

## Reporting

State the input size and environment of any measurement. If you could not measure, mark the finding **Needs verification** and give the exact command the user can run.
