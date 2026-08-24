#!/usr/bin/env python3
"""Run executable properties and preserve a terminal result record."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results/05_PROPERTY_TEST_RESULTS.txt"


def main() -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    command = [sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"]
    result = subprocess.run(command, text=True, capture_output=True, env=env, check=False)
    content = (
        f"PROPERTY_TEST_EXIT_CODE={result.returncode}\n"
        f"PROPERTY_TEST_STATUS={'PASS' if result.returncode == 0 else 'FAIL'}\n\n"
        f"STDOUT\n{result.stdout}\nSTDERR\n{result.stderr}"
    )
    OUT.write_text(content, encoding="utf-8")
    print(f"PROPERTY_TEST_STATUS={'PASS' if result.returncode == 0 else 'FAIL'}")
    print(f"PROPERTY_TEST_RECORD={OUT}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

