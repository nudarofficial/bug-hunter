# Skill Test Results (v1.0.0 → v1.0.1)

This page records how Bug Hunter v1.0.0 was tested against bugs it had never seen and what changed because of it. The failure output and numbers below were all observed while running the tests.

## Method

1. **Discovery.** The skill was copied into a test project's `.claude/skills/bug-hunter/` and Claude Code was started headlessly (`claude -p`). The session's skill list included `bug-hunter`, so the folder layout and frontmatter are accepted. The full headless run then stopped, because the Claude Code CLI on the test machine was not signed in. Automatic triggering from a prompt was therefore **not** verified end to end.
2. **Behavior.** Each scenario ran in a fresh Claude agent (Opus 5.5) with no knowledge of the planted bugs. The agent loaded `SKILL.md` the way Claude Code does when the skill triggers, followed it, and read reference files only when the skill pointed to them. At the end it reported any instructions that were unclear.
3. **Independent check.** The test author re-ran each agent's tests and repeated its reproductions before accepting the result.

## Scenarios and results

### A. Python: "page 2 shows only 5 of 25 products; the test fails. Fix it."

Planted bugs: 0-based offset for 1-based pages, and `total_pages` rounding down.

| Expected behavior | Result |
|---|---|
| Reproduce the failure before changing code | ✅ Ran the test (`AssertionError: 5 != 10`) and printed actual page contents |
| Find the root cause, not the symptom | ✅ `start = page * page_size` with 1-based pages |
| Notice the related second defect | ✅ Found `total_pages` floor division (2 pages reported for 25 items) |
| Separate confirmed findings from potential ones | ✅ Two Confirmed; missing `page < 1` validation reported as a Potential risk and left unchanged |
| Minimal fix | ✅ Two one-line changes; no signature changes |
| Regression tests | ✅ Added 3 tests, all 4 pass (re-run independently: 4/4 OK) |
| Honest verification report | ✅ Stated that it did not run the new tests against the old code |

### B. JavaScript: "Find bugs in cart.js."

Planted bugs: `<=` loop bound, discount applied by mutating the cart, inherited keys in a plain-object lookup, and an unbounded cache.

| Expected behavior | Result |
|---|---|
| Review only; leave the code unchanged | ✅ `cart.js` left unchanged; fixes proposed as a diff |
| Confirm by running code | ✅ Ran every finding with Node v26.13.0; scratch script deleted afterwards |
| Find the crash | ✅ `cartTotal` throws on every input, including `[]` |
| Find subtler defects | ✅ Codes `"toString"`/`"constructor"`/`"__proto__"` give `NaN`; discounts stack (VIP25 twice → 56.25); `getUserCart('__proto__')` returns `Object.prototype` |
| Label uncertain items | ✅ Cache growth, cached rejected promises, and float money listed as Potential risks with conditions |

All four confirmed findings were reproduced independently.

### C. No evidence: "My Go service crashes sometimes. What does the stack trace say? Fix it."

No code or trace was provided.

| Expected behavior | Result |
|---|---|
| Do not invent a trace, cause, or fix | ✅ Said plainly that no trace or code was available |
| Ask for the right evidence | ✅ Full panic output, `GOTRACEBACK=all`, code plus callers, Go version, when it happens |
| Keep hypotheses labelled | ✅ Common Go crash causes mentioned only as things the trace would confirm or rule out |

## Changes made in v1.0.1 from this feedback

The agents' notes on unclear or missing instructions led to these changes:

- **"Not enough evidence" route**: explicit stop-and-ask behavior, plus a per-language table for collecting traces.
- **Edit vs. report**: "fix" requests change code; "find/review" requests propose fixes only.
- **Second defects**: fix them only when they are part of the reported symptom; otherwise report them.
- **One status vocabulary**: Confirmed findings now say *how* they were confirmed (reproduced / observed / traced, not executed).
- **Report format**: compact for one finding, full template led by the findings table for several.
- **Tests**: show the failure before the fix when feasible; what to do when the project has no test framework.
- **Regression review**: call out observable behavior changes and the callers that must adapt.
- **Severity without callers**: rate by the most plausible usage and state the assumption.
- **Scratch files**: keep them out of the project or delete them, and mention them.
- **New pitfalls**: an "All languages" section (off-by-one bounds, truthiness checks, argument mutation, caches, float money), and JavaScript plain-object-as-map hazards.

## Limitations of this test

- Three scenarios on one model. Anthropic recommends testing each model you plan to use (Haiku, Sonnet, Opus).
- Automatic triggering was not verified end to end because the CLI could not sign in on the test machine. Only discovery was confirmed.
