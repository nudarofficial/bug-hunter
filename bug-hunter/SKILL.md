---
name: bug-hunter
description: Investigates and fixes software bugs through evidence-based root-cause analysis. Reads stack traces, logs, and error messages; traces logic, runtime, concurrency, security, and performance defects across files; proposes minimal fixes with a regression review and targeted tests. Use when the user reports a bug, crash, exception, failing test, wrong output, flaky behavior, or slowdown, or asks to debug code, find bugs, or review code for defects in Python, JavaScript, TypeScript, Java, C, C++, C#, Go, Rust, PHP, Ruby, or SQL.
---

# Bug Hunter

Find the root cause of a defect, fix it with the smallest sound change, and report exactly what was and was not verified.

## Non-negotiable rules

1. **Never invent evidence.** Do not fabricate stack traces, error messages, log lines, test results, reproductions, benchmark numbers, or CVE identifiers. If something was not run or observed, say so.
2. **Separate confirmed from suspected.** A finding is *Confirmed* only when backed by an observed failure, a reproduced run, or an unambiguous code path. Everything else is a *Potential risk* or *Needs verification*.
3. **Fix the cause, not the symptom.** Do not wrap errors in `try/except`, add null checks, or bump timeouts unless the analysis shows that is the actual cause.
4. **Stay in scope.** Do not refactor, reformat, rename, or "improve" unrelated code. Do not delete data, rewrite git history, change dependencies, or run destructive commands without the user's explicit permission.
5. **Label assumptions.** When the runtime version, configuration, input data, or caller behavior is unknown, state the assumption next to the conclusion that depends on it.

## Workflow

Copy this checklist and track progress for any non-trivial bug:

```
Bug Hunt Progress:
- [ ] 1. Define the bug (observed vs expected)
- [ ] 2. Gather evidence (code, traces, logs, inputs, versions)
- [ ] 3. Reproduce or trace the failure
- [ ] 4. Form and test hypotheses; identify root cause
- [ ] 5. Classify findings (confirmed / potential / ruled out)
- [ ] 6. Design the minimal fix
- [ ] 7. Review the fix for regressions
- [ ] 8. Add or recommend tests; run them if permitted
- [ ] 9. Report results and verification status
```

### 1. Define the bug

Write one sentence each for **observed behavior**, **expected behavior**, and **trigger conditions** (inputs, environment, frequency). If expected behavior is ambiguous, ask before changing code. For "find bugs in this code" requests with no report, infer the intended behavior from names, docs, tests, and callers, and state that inference.

### 2. Gather evidence

- Read the failing code **and** its callers, callees, and the data it consumes. Bugs often live one hop away from where they surface.
- For a stack trace, find the deepest frame in project code (not library code) and the first frame where state became wrong. See [reference/stack-traces.md](reference/stack-traces.md).
- Note language/runtime version, framework, and configuration when they affect semantics (for example Go < 1.22 loop variables, Python 2 vs 3 division, JavaScript `==`).
- Check recent changes if version control is available (`git log -p -- <file>`, `git blame`, `git bisect` for regressions).

### 3. Reproduce or trace

Prefer, in order:

1. Run the existing failing test or command.
2. Write the smallest script or test that triggers the failure.
3. If execution is not possible (no permissions, missing services, no toolchain), trace the path manually: list each step with the concrete value of the relevant variables. Mark the result **"traced, not executed"**.

Never report a reproduction that was not actually run.

### 4. Find the root cause

- State a hypothesis that explains **all** observed symptoms, not just the last one.
- Test it: add a targeted assertion or log, narrow inputs, or bisect. Discard hypotheses the evidence contradicts and say why.
- Ask "why" until you reach a defect in code, configuration, data, or contract — not a restatement of the symptom. "Variable is `None`" is a symptom; "the cache returns `None` on a miss and the caller assumes a hit" is a cause.
- Check whether the same defect pattern exists elsewhere (grep for the same call, idiom, or copied block). Report other occurrences as separate findings.

Language-specific traps: [reference/language-pitfalls.md](reference/language-pitfalls.md).
Security defects: [reference/security.md](reference/security.md).
Performance defects: [reference/performance.md](reference/performance.md).

### 5. Classify findings

| Status | Meaning |
|---|---|
| **Confirmed** | Reproduced, observed in the provided trace/log, or a deterministic code path proves it. |
| **Potential risk** | Plausible under conditions not shown (specific input, load, configuration). Name those conditions. |
| **Needs verification** | Depends on information you do not have. Say what would settle it. |
| **Ruled out** | A hypothesis you checked and rejected. Include it when it saves the user time. |

Assign severity by impact, not by how interesting the bug is:

| Severity | Typical impact |
|---|---|
| **Critical** | Data loss or corruption, remote code execution, auth bypass, crash of a core path for all users |
| **High** | Wrong results on common paths, exploitable injection, crash on realistic inputs, resource leak that exhausts the service |
| **Medium** | Wrong results on edge cases, degraded performance under load, missing validation with limited blast radius |
| **Low** | Cosmetic issues, misleading messages, minor inefficiency, code smell with a plausible future failure |

### 6. Design the minimal fix

- Change the fewest lines that remove the root cause. Keep existing style, naming, and public interfaces.
- If the proper fix is large (schema change, API change, architectural), propose it and, when useful, a clearly labelled short-term mitigation.
- When more than one fix is reasonable, recommend one and state the trade-off in a sentence.
- Show the fix as a unified diff or as the complete corrected function — whichever is clearer for the change size.

### 7. Review for regressions

Before presenting the fix, check:

- [ ] Every caller of the changed function still gets the behavior it relies on (return type, `None`/`null` handling, exceptions raised, ordering).
- [ ] Boundary inputs: empty, single element, maximum size, negative, zero, Unicode, `None`/`null`/`undefined`.
- [ ] Concurrency: shared state, ordering, cancellation, retries.
- [ ] Error paths still release resources (files, locks, connections, transactions).
- [ ] Security posture is unchanged or improved (no new injection, no disabled validation).
- [ ] Performance is not made asymptotically worse.

### 8. Tests

- Add a regression test that **fails before the fix and passes after**. Name it after the behavior, not the ticket.
- Use the project's existing test framework and conventions. Do not add a new framework.
- Run the tests only when the environment allows and the user has not forbidden it. Report the exact command and the actual outcome; if not run, say "not run" and give the command.

### 9. Report

Use the structure in [reference/report-template.md](reference/report-template.md). For a single small bug, a compact version is fine:

```markdown
**Root cause:** <one or two sentences>
**Status:** Confirmed (reproduced with `<command>`) | Traced, not executed | Suspected
**Fix:** <diff or corrected code>
**Regression check:** <what was considered>
**Tests:** <added test name> — <passed / failed / not run, and the command>
**Not verified:** <anything left open>
```

## Request types

**"Here is an error / stack trace"** → Steps 1–9, starting from the trace.

**"Find bugs in this file / review this code"** → Read the whole unit plus its interfaces, then list findings sorted by severity. Each finding: location (`file:line`), status, severity, evidence, fix. Do not pad the list with style nits; group minor items under "Low-priority notes" or omit them.

**"This test is flaky"** → Look for time, randomness, ordering (dict/set/hash iteration, parallel tests), shared state between tests, network, and unawaited async work. Prove the source by controlling it (fixed seed, frozen clock, isolated state).

**"It got slow"** → Measure before claiming; see [reference/performance.md](reference/performance.md). Never quote a speedup you did not measure.

**"Is this secure?"** → Follow [reference/security.md](reference/security.md). Report only issues with a concrete attack path or clearly unsafe pattern; label the rest as hardening suggestions.

## Worked examples

See [reference/examples.md](reference/examples.md) for complete bug reports across Python, JavaScript, TypeScript, Java, Go, C, C++, C#, Rust, PHP, Ruby, and SQL, showing confirmed findings, potential risks, and minimal fixes.
