# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/nudarofficial/bug-hunter/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/nudarofficial/bug-hunter/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/nudarofficial/bug-hunter/releases/tag/v1.0.0
