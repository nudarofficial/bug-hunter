# Bug Hunter: a Claude Agent Skill for Debugging and Root-Cause Analysis

[![CI](https://github.com/nudarofficial/bug-hunter/actions/workflows/ci.yml/badge.svg)](https://github.com/nudarofficial/bug-hunter/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/nudarofficial/bug-hunter)](https://github.com/nudarofficial/bug-hunter/releases)

**Bug Hunter** is an open-source [Agent Skill](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) for Claude. It brings a disciplined debugging process to Claude Code, claude.ai, and the Claude API. Claude uses it to investigate bugs, read stack traces and logs, find the root cause, and propose the smallest fix that solves it. Every report states what was verified and what was not.

It is built for one job: accurate debugging. It favors evidence over guesses and minimal fixes over rewrites. It reports honestly when something could not be checked.

## Contents

- [Why Bug Hunter](#why-bug-hunter)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Example input and output](#example-input-and-output)
- [Supported languages](#supported-languages)
- [Project structure](#project-structure)
- [Validation and testing](#validation-and-testing)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)

## Why Bug Hunter

AI debugging help often goes wrong in a few predictable ways:

- it guesses a cause without evidence
- it patches the symptom
- it rewrites unrelated code
- it says "tests pass" when nothing was run

Bug Hunter gives Claude explicit rules against each of these:

- **Root cause, not symptom.** A hypothesis must explain every observed symptom before a fix is proposed.
- **Confirmed vs. potential.** Each finding is labelled *Confirmed*, *Potential risk*, *Needs verification*, *Ruled out*, or *Traced, not executed*.
- **No fabricated evidence.** Claude never invents stack traces, error messages, test results, reproductions, or performance numbers.
- **Minimal, reviewed fixes.** The smallest change that removes the cause, then a regression checklist covering callers, edge cases, concurrency, error paths, security, and performance.
- **Stays in scope.** No unrelated refactoring and no destructive commands without permission.

## Features

- Bug detection and code review for defects, with findings sorted by severity (Critical / High / Medium / Low)
- Root-cause analysis for logic, runtime, concurrency, security, and performance issues
- Reading stack traces, logs, and error messages, including chained exceptions and async traces
- Tracing interactions across files and components (callers, callees, data origin)
- Minimal fixes as unified diffs or corrected functions
- A regression review for every fix
- Test recommendations: a regression test that fails before the fix and passes after
- Flaky-test investigation (time, randomness, ordering, shared state, unawaited async work)
- Performance investigation that measures before it claims, with per-language profiler commands
- Security investigation using source → propagation → sink analysis

## Installation

The installable skill is the [`bug-hunter/`](bug-hunter) folder. Each Claude surface manages skills separately; see [Anthropic's documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#where-skills-work).

### Claude Code

Personal install, available in all projects:

```bash
git clone https://github.com/nudarofficial/bug-hunter.git
mkdir -p ~/.claude/skills
cp -r bug-hunter/bug-hunter ~/.claude/skills/
```

On Windows PowerShell:

```powershell
git clone https://github.com/nudarofficial/bug-hunter.git
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse bug-hunter\bug-hunter "$HOME\.claude\skills\"
```

For a single project, copy the folder to `.claude/skills/bug-hunter/` in that repository instead. You can also download `bug-hunter-v1.0.0.zip` from [Releases](https://github.com/nudarofficial/bug-hunter/releases) and unzip it into the skills directory. Either way you should end up with `~/.claude/skills/bug-hunter/SKILL.md`.

### claude.ai

1. Download `bug-hunter-v1.0.0.zip` from [Releases](https://github.com/nudarofficial/bug-hunter/releases).
2. Upload it in the Skills section of claude.ai Settings. Custom skills need a plan with code execution enabled; see Anthropic's help article [Using Skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude).

### Claude API

Upload the `bug-hunter` folder with the Skills API (`/v1/skills`). Then reference it in the `container` parameter together with the code execution tool. See [Using Agent Skills with the API](https://platform.claude.com/docs/en/build-with-claude/skills-guide).

### Verify a release download

```bash
sha256sum -c bug-hunter-v1.0.0.zip.sha256
```

## Usage

The skill triggers on its own when your request matches its description. You don't need any special syntax. Example requests:

- "This test fails with `KeyError: 'region'`. Here's the traceback. Find the cause."
- "Find bugs in `src/billing/invoice.ts`."
- "Our `/orders` endpoint got slow after yesterday's deploy."
- "This Go test is flaky on CI but passes locally."
- "Is this PHP login handler secure?"

In Claude Code you can also invoke it directly with `/bug-hunter`.

## Example input and output

**Input**

> The checkout total is always 0, but the item service logs show every price being fetched.
>
> ```js
> async function totalPrice(ids, fetchItem) {
>   let total = 0;
>   ids.forEach(async (id) => {
>     const item = await fetchItem(id);
>     total += item.priceCents;
>   });
>   return total;
> }
> ```

**Output (abridged)**

> **Root cause:** `forEach` discards the promises returned by the `async` callback, so `return total` runs before any `await fetchItem(...)` resolves. The fetches finish later, which is why the logs look healthy.
>
> **Status:** Confirmed (reproduced with `node examples/javascript-async-foreach/test_example.js`)
>
> **Fix:**
> ```diff
> -  let total = 0;
> -  ids.forEach(async (id) => {
> -    const item = await fetchItem(id);
> -    total += item.priceCents;
> -  });
> -  return total;
> +  const items = await Promise.all(ids.map((id) => fetchItem(id)));
> +  return items.reduce((sum, item) => sum + item.priceCents, 0);
> ```
>
> **Trade-off:** `Promise.all` fetches concurrently. If the service is rate-limited, use a `for...of` loop with `await`.
>
> **Regression check:** an empty list still returns 0. Fetch errors now reject instead of being lost as unhandled rejections.

More complete reports:

- [Python: mutable default argument](examples/python-mutable-default/README.md)
- [Python + SQL: injection and missing-row crash](examples/python-sql-injection/README.md)
- [JavaScript: async callback in `forEach`](examples/javascript-async-foreach/README.md)
- [Worked examples in 12 languages](bug-hunter/reference/examples.md)

## Supported languages

| Language | Coverage in the skill |
|---|---|
| Python | Pitfalls, stack traces, worked + runnable examples |
| JavaScript | Pitfalls, stack traces, worked + runnable examples |
| TypeScript | Pitfalls (type-system escape hatches), worked example |
| Java | Pitfalls, stack traces, worked example |
| C | Pitfalls, sanitizer guidance, worked example |
| C++ | Pitfalls, sanitizer guidance, worked example |
| C# | Pitfalls, stack traces, worked example |
| Go | Pitfalls (including version-dependent loop semantics), panics, worked example |
| Rust | Pitfalls, panics, worked example |
| PHP | Pitfalls, stack traces, worked example |
| Ruby | Pitfalls, stack traces, worked example |
| SQL | Pitfalls (NULL semantics, joins, races), query plans, worked example |

The workflow itself does not depend on the language. Framework-specific knowledge comes from Claude's general training, not from this skill. The skill makes no claims about particular frameworks beyond the patterns listed in its reference files.

## Project structure

```text
bug-hunter/                      repository root
├── bug-hunter/                  the installable skill
│   ├── SKILL.md                 workflow, rules, status and severity scales
│   └── reference/               loaded only when needed
│       ├── stack-traces.md      reading traces and logs by language
│       ├── language-pitfalls.md bug patterns for 12 languages
│       ├── security.md          source → sink investigation
│       ├── performance.md       measure-first performance debugging
│       ├── report-template.md   full report structure
│       └── examples.md          worked examples
├── examples/                    runnable buggy-vs-fixed cases with tests
├── evals/evals.json             evaluation scenarios (rubrics)
├── scripts/
│   ├── validate_skill.py        frontmatter, structure, and link validation
│   ├── run_examples.py          runs example regression tests
│   └── build_release.py         reproducible ZIP + SHA-256 checksum
├── tests/                       unit tests for the scripts
├── docs/releases/               release notes
└── .github/                     CI workflow, issue and PR templates
```

The skill follows Anthropic's [Agent Skills structure](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#skill-structure) and [authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):

- `name` and `description` in the YAML frontmatter
- `SKILL.md` body under 500 lines
- reference files linked one level deep from `SKILL.md`
- tables of contents in long reference files
- forward-slash paths
- no executable code inside the skill

## Validation and testing

```bash
python scripts/validate_skill.py           # SKILL.md metadata, structure, links
python -m unittest discover -s tests -v    # script unit tests
python scripts/run_examples.py             # example regression tests (Node.js 18+ for JS)
python scripts/build_release.py --version 1.0.0   # build and verify the release ZIP
```

The validator checks the documented frontmatter rules:

- `name`: at most 64 characters; lowercase letters, numbers, and hyphens only; no XML tags; no reserved words
- `description`: not empty; at most 1024 characters; no XML tags

It also checks body length, one-level-deep references, tables of contents, and every relative link in the repository. [GitHub Actions](https://github.com/nudarofficial/bug-hunter/actions/workflows/ci.yml) runs all of these on Ubuntu and Windows.

## Limitations

- **It guides Claude; it is not an analyzer.** Bug Hunter is a set of instructions. It does not include a static analyzer, debugger, or fuzzer. What Claude can actually run depends on the surface and your permissions. For example, the Claude API code-execution sandbox has no network access.
- **Verification depends on the environment.** If code cannot be executed, conclusions are labelled "Traced, not executed". Treat them as well-reasoned hypotheses.
- **Runnable examples cover Python and JavaScript only.** The other worked examples are explanations that were not executed.
- **No built-in evaluation runner.** `evals/evals.json` contains rubric-style scenarios for manual testing or your own harness.
- **Results vary by model.** Anthropic recommends testing skills with each model you plan to use.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow and the rules for examples and reference material. Report security concerns as described in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © nudarofficial
