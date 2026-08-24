#!/usr/bin/env python3
"""Run microbenchmark unit tests and preserve their output."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results/05_UNIT_TEST_RESULTS.txt"


def main() -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    OUT.write_text(
        f"UNIT_TEST_EXIT_CODE={result.returncode}\n"
        f"UNIT_TEST_STATUS={'PASS' if result.returncode == 0 else 'FAIL'}\n\n"
        f"STDOUT\n{result.stdout}\nSTDERR\n{result.stderr}",
        encoding="utf-8",
    )
    print(f"UNIT_TEST_STATUS={'PASS' if result.returncode == 0 else 'FAIL'}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

