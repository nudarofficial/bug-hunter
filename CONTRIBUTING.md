# Contributing to Bug Hunter

Contributions are welcome. The skill is most useful when it is accurate, concise, and grounded in real debugging cases. Bulk does not make it better.

## Ground rules

- **Accuracy first.** Every technical claim must be correct. Label version-specific behavior with the version, for example "Go < 1.22" or "PHP 8+".
- **No invented evidence.** Examples must not contain fabricated benchmark numbers, CVE identifiers, or tool output that was never produced.
- **Keep `SKILL.md` lean.** Its body must stay under 500 lines. Put detailed material in `bug-hunter/reference/` and link it directly from `SKILL.md`. Reference files must not link to further files.
- **One concern per pull request.**

## Development setup

You need Python 3.9 or later. Node.js 18 or later is only needed for the JavaScript example. Nothing else has to be installed. PyYAML is optional; when present, the validator uses it for stricter frontmatter parsing.

```bash
python scripts/validate_skill.py           # SKILL.md metadata, structure, links
python -m unittest discover -s tests -v    # tests for the scripts
python scripts/run_examples.py             # buggy-vs-fixed example tests
python scripts/build_release.py --version 0.0.0 --out dist   # build + verify ZIP
```

CI runs the same commands on every push and pull request.

## Adding a runnable example

Create `examples/<language>-<bug-name>/` containing:

| File | Purpose |
|---|---|
| `README.md` | The bug report (input) and the Bug Hunter report (output), using the format in `bug-hunter/reference/report-template.md` |
| `buggy.*` | Minimal code that has the defect |
| `fixed.*` | The minimal correct fix |
| `test_example.py` or `test_example.js` | A test that **demonstrates the bug in `buggy`** and **passes on `fixed`** |

The test runner picks up `test_example.py` and `test_example.js` automatically. Use only the standard library, or `node:test` for JavaScript.

## Adding an evaluation scenario

Add an entry to `evals/evals.json` with `id`, `skills`, `query`, `files`, and `expected_behavior`. Agent Skills has no built-in evaluation runner, so these scenarios are rubrics for manual or scripted testing with different models.

## Releasing (maintainers)

1. Move the "Unreleased" entries in `CHANGELOG.md` under the new version.
2. Add release notes under `docs/releases/`.
3. Run `python scripts/build_release.py --version X.Y.Z`.
4. Create a GitHub release tagged `vX.Y.Z`. Attach `dist/bug-hunter-vX.Y.Z.zip` and `dist/bug-hunter-vX.Y.Z.zip.sha256`.

## License

By contributing, you agree that your contributions are licensed under the MIT License.
