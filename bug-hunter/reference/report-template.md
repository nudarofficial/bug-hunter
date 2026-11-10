# Bug Report Template

Use this structure for full investigations. Drop sections that do not apply; never fill a section with invented content.

````markdown
## Summary
<One or two sentences: what is broken, the root cause, and the fix.>

## Bug definition
- **Observed:** <what happens, quoting the exact error if any>
- **Expected:** <what should happen>
- **Trigger:** <inputs / environment / frequency>

## Evidence
- <file:line> — <what the code does here>
- <trace / log excerpt exactly as provided or observed>
- <reproduction command and its actual output, or "not executed">

## Root cause
<Explanation that accounts for every symptom. Name the defect in code, configuration, data, or contract.>

## Findings
| # | Location | Status | Severity | Description |
|---|---|---|---|---|
| 1 | `path/file.ext:42` | Confirmed | High | <short description> |
| 2 | `path/other.ext:10` | Potential risk | Medium | <condition under which it fails> |

**Ruled out:** <hypotheses checked and rejected, with the reason>

## Fix
```diff
- old line
+ new line
```
<Why this is the minimal correct change. Trade-offs if any.>

## Regression review
- Callers checked: <list>
- Edge cases considered: <list>
- Side effects: <none found / list>

## Tests
- Added: `<test name>` — fails before the fix, passes after.
- Ran: `<exact command>` → <actual result>   (or: **Not run** — <reason>)

## Verification status
- **Verified:** <what was actually executed or observed>
- **Not verified:** <what remains assumed, and how to check it>
- **Assumptions:** <runtime version, configuration, input shape, etc.>
````

## Status vocabulary

Use exactly these terms so readers can scan reports consistently:

- **Confirmed** — reproduced, observed in provided evidence, or proven by a deterministic code path.
- **Potential risk** — plausible under named conditions not shown.
- **Needs verification** — cannot be decided with available information; state what would decide it.
- **Ruled out** — checked and rejected.
- **Traced, not executed** — conclusion reached by reading code, without running it.
