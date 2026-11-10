#!/usr/bin/env python3
"""Run the regression tests for every runnable example under examples/.

Each example directory contains a buggy version, a fixed version, and a test
that proves the bug exists in the buggy version and is gone in the fixed one.

  * examples/*/test_example.py  -> run with the current Python interpreter
  * examples/*/test_example.js  -> run with `node` (Node.js 18+ for node:test)

Usage:
    python scripts/run_examples.py [--require-node]

Without --require-node, JavaScript examples are reported as SKIPPED when
`node` is not on PATH. With it, a missing Node.js counts as a failure (CI).
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
# Generous limit: each example finishes in well under a second.
TIMEOUT_SECONDS = 120


def run(cmd: list[str]) -> tuple[bool, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return False, f"timed out after {TIMEOUT_SECONDS}s"
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run example regression tests.")
    parser.add_argument("--require-node", action="store_true",
                        help="fail instead of skipping when Node.js is not installed")
    args = parser.parse_args(argv)

    node = shutil.which("node")
    results = []
    for test in sorted(EXAMPLES.glob("*/test_example.*")):
        name = test.parent.name
        if test.suffix == ".py":
            ok, output = run([sys.executable, "-I", str(test)])
        elif test.suffix == ".js":
            if node is None:
                status = "FAIL" if args.require_node else "SKIPPED"
                results.append((name, status, "node not found on PATH"))
                continue
            ok, output = run([node, str(test)])
        else:
            continue
        results.append((name, "PASS" if ok else "FAIL", output))

    if not results:
        print("No example tests found.")
        return 1

    for name, status, output in results:
        print(f"[{status}] {name}")
        if status != "PASS":
            for line in output.splitlines()[-30:]:
                print(f"    {line}")
    failed = sum(1 for _, status, _ in results if status == "FAIL")
    skipped = sum(1 for _, status, _ in results if status == "SKIPPED")
    passed = len(results) - failed - skipped
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
