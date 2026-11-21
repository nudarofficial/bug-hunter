# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.3] - 2026-11-21

### Changed
- The `SKILL.md` description now says to use the skill "even when the bug looks small or obvious". In end-to-end Claude Code CLI tests this made the skill trigger automatically for a code review. Before, it triggered in none of the three scenarios.
- New non-negotiable rule 8 in `SKILL.md`: every fix gets a regression test that is run before and after the fix, or the report says why not. In testing, explicit `/bug-hunter` runs skipped the test before this rule and added one after it.
- README: recommends invoking the skill with `/bug-hunter`, and documents that automatic triggering is not guaranteed.

### Added
- `docs/skill-test-results.md`: results of the end-to-end Claude Code CLI runs.

## [1.0.2] - 2026-11-21

### Fixed
- `SKILL.md` step 8 suggested `git stash` to show that a new test fails before the fix. Stashing would also hide the new test, so the step now says to write and run the test before applying the fix.
- CI warned that its actions run on deprecated Node.js 20. They are updated to `actions/checkout@v5`, `actions/setup-python@v6`, and `actions/setup-node@v5`, and the JavaScript example now runs on Node.js 24 LTS.
- `CONTRIBUTING.md` claimed Python 3.9 support, which was never tested. The minimum is now 3.10, and CI tests both 3.10 and 3.13.
- The issue template's surface placeholder named a made-up Claude Code version.

### Added
- `CODE_OF_CONDUCT.md`.
- Dependabot configuration that keeps GitHub Actions versions current.
- A fuller project tree in the README.

## [1.0.1] - 2026-11-10

### Changed
- Copyright holder is now "Nudar" (LICENSE, README).
- `SKILL.md` was clarified using feedback from testing on unseen bugs; see [docs/skill-test-results.md](docs/skill-test-results.md):
  - new "Not enough evidence" request type
  - edit-only-when-asked rule, and cleanup of scratch files
  - rules for second defects
  - Confirmed findings now state how they were confirmed
  - report format chosen by the number of findings
  - test guidance for projects without a test framework
  - regression review now covers behavior changes
  - severity when callers are unknown
- `reference/report-template.md`: status vocabulary aligned with `SKILL.md`.

### Added
- `reference/stack-traces.md`: per-language guide to collecting a usable trace.
- `reference/language-pitfalls.md`: "All languages" section, and JavaScript plain-object-as-map hazards.
- `docs/skill-test-results.md`: test method, results, and limitations.

## [1.0.0] - 2026-11-10

### Added
- `bug-hunter` Agent Skill (`SKILL.md`) with a nine-step debugging workflow: bug definition, evidence gathering, reproduction or tracing, root-cause analysis, finding classification, minimal fix, regression review, tests, and verification reporting.
- Status vocabulary (Confirmed, Potential risk, Needs verification, Ruled out, Traced, not executed) and a severity scale.
- Reference files: stack-trace and log reading, language pitfalls for 12 languages, security investigation, performance investigation, report template, and worked examples.
- Runnable buggy-versus-fixed examples for Python and JavaScript, each with regression tests.
- Evaluation scenarios in `evals/evals.json`.
- Scripts that validate the skill, run the examples, and build a reproducible release ZIP with a SHA-256 checksum.
- GitHub Actions CI, issue templates, and a pull request template.

[Unreleased]: https://github.com/nudarofficial/bug-hunter/compare/v1.0.3...HEAD
[1.0.3]: https://github.com/nudarofficial/bug-hunter/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/nudarofficial/bug-hunter/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/nudarofficial/bug-hunter/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/nudarofficial/bug-hunter/releases/tag/v1.0.0
