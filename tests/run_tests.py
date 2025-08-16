#!/usr/bin/env python3
"""Ultra-minimal test runner ensuring only fast, lean tests execute by default.

Usage:
  python tests/run_tests.py            # run fast suite
  python tests/run_tests.py --all      # run all (including skipped markers if present)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List


def _run(cmd: List[str]) -> int:
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Run full suite (currently same as fast if no extra tests).")
    args = parser.parse_args()

    base = [sys.executable, "-m", "pytest", "-q"]
    if not args.all:
        # Default filter keeps suite tiny & fast; adjust if markers added later.
        base += ["-m", "not slow and not integration and not performance"]
    return _run(base)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
