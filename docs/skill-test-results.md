# Skill Test Results

This page records how Bug Hunter was tested against bugs it had never seen and what changed because of it. The first round (simulated loading, v1.0.0 → v1.0.1) comes first. The end-to-end Claude Code CLI round (v1.0.2 → v1.0.3) follows it. The failure output and numbers below were all observed while running the tests.

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

## Real Claude Code CLI test (v1.0.2 → v1.0.3)

Once the Claude Code CLI was signed in, the three scenarios were run end to end. Each used `claude -p` with the skill installed in `.claude/skills/bug-hunter/` and the model `claude-sonnet-5-5`. The prompts did not mention the skill.

### Automatic triggering

| Scenario | v1.0.2 description | v1.0.3 description ("…even when the bug looks small or obvious") |
|---|---|---|
| Python fix | Not triggered | Not triggered |
| JavaScript review | Not triggered | **Triggered automatically**. Followed the skill's format: findings table, status labels, "traced, not executed" |
| No evidence (Go crash) | Not triggered | Not triggered |

Without the skill, Claude still found the bugs and invented nothing, but it skipped steps the skill requires:
- In the Python case it added no regression test.
- In the JavaScript case it ran nothing to confirm the findings.

**Conclusion:** Claude decides for itself when to load a skill, and it often skips skills for tasks that look simple. The stronger description helps but does not guarantee use. Invoking the skill explicitly does: start the request with `/bug-hunter` or say "use bug-hunter".

### Explicit invocation (`/bug-hunter …`)

| Version | Result |
|---|---|
| v1.0.2 | Followed the skill: compact report, status labels, second defect (`total_pages`) reported but left unchanged because it was outside the symptom. It **added no regression test**. |
| v1.0.3, with the new rule 8 "Every fix gets a regression test" | Ran the failing test first (`AssertionError: 5 != 10`), made a one-line fix, **added a regression test**, and reported the second defect without changing it. It stated that the new test had not been run against the unfixed code. The tests were re-run independently: 2/2 pass. |

## Three models, v1.0.3 (Haiku 5.5, Sonnet 5.5, Opus 5.5)

The same scenarios ran on v1.0.3 in the Claude Code CLI for each model. Every run started from a fresh copy of the buggy code with the skill installed as a project skill. The test author re-ran every test suite that a run modified and checked that review-only runs left the code unchanged.

| Scenario | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 |
|---|---|---|---|
| **`/bug-hunter` + Python fix** | ✅ Reproduced (`5 != 10`), one-line fix, regression test added, `total_pages` reported only. 2/2 tests pass | ✅ Same behavior. 2/2 tests pass | ✅ Same behavior. 2/2 tests pass |
| **Python fix, skill not named** | Not triggered. Correct fix, no new test | Not triggered. Correct fix, no new test | Not triggered. Correct fix, no new test |
| **"Find bugs in cart.js", skill not named** | Not triggered. Found and ran 6 issues; code unchanged | **Triggered**. Findings table with status labels; traced, not executed | **Triggered**. Ran every finding; code unchanged; scratch script removed |
| **Go crash, no evidence** | Not triggered. Invented nothing; asked for trace, code, version | Not triggered. Same | Not triggered. Same |

Cost per run ranged from about US$0.01 (Haiku) to US$0.76 (Opus).

**What this shows**

- **Explicit invocation works on all three models.** With `/bug-hunter`, each model reproduced the failure first, made the minimal fix, added a regression test, reported the out-of-scope defect without changing it, and stated what it had not verified.
- **Automatic triggering is partial.** It happened for the code-review request on Sonnet and Opus (2 of 9 automatic runs). Without the skill the fixes were still correct, but no model added a regression test. That gap is what the skill closes.
- **No model invented evidence**, with or without the skill.

## Limitations of this test

- Few scenarios: two languages plus a no-evidence case.
- Fable 5.2 was not tested, because it required extra usage credits on the test account.
- Automatic triggering depends on the model and the request, so results on other tasks may differ.
