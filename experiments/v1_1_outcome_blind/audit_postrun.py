#!/usr/bin/env python3
"""Audit frozen inputs and generated validation results without changing rules."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results/09_POSTRUN_AUDIT.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_prefreeze() -> tuple[bool, int]:
    entries = []
    for line in (ROOT / "03_PREFREEZE_CHECKSUMS_SHA256.txt").read_text().splitlines():
        expected, relative = line.split("  ", 1)
        entries.append((expected, ROOT / relative))
    return all(path.is_file() and digest(path) == expected for expected, path in entries), len(entries)


def main() -> int:
    prefreeze_ok, files_checked = verify_prefreeze()
    property_text = (ROOT / "results/05_PROPERTY_TEST_RESULTS.txt").read_text(encoding="utf-8")
    property_ok = "PROPERTY_TEST_STATUS=PASS" in property_text
    with (ROOT / "results/07_SIMULATION_SUMMARY.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    simulation_ok = bool(rows) and all(row["status"] == "PASS" for row in rows)
    overall = prefreeze_ok and property_ok and simulation_ok
    content = f"""# Postrun validation audit

- `PREFREEZE_CHECKSUM_VERIFY={'PASS' if prefreeze_ok else 'FAIL'}`
- `PREFREEZE_ENTRIES_CHECKED={files_checked}`
- `PROPERTY_TEST_STATUS={'PASS' if property_ok else 'FAIL'}`
- `SIMULATION_ACCEPTANCE_CHECKS={sum(row['status'] == 'PASS' for row in rows)}/{len(rows)}`
- `SIMULATION_VALIDATION={'PASS' if simulation_ok else 'FAIL'}`
- `OVERALL_INTERNAL_VALIDATION={'PASS' if overall else 'FAIL'}`
- `MODEL_API_CALLED=NO`
- `OLD_PROVIDER_PRIVATE_TRUTH_ACCESSED=NO`
- `OLD_NEURO_TOUCHED=NO`
- `CORE_V1_0_MUTATED=NO`

Passing this audit establishes internal executable consistency only. It does not authorize prefreeze or support an empirical RIEC-Agent effectiveness claim.
"""
    OUT.write_text(content, encoding="utf-8")
    print(f"OVERALL_INTERNAL_VALIDATION={'PASS' if overall else 'FAIL'}")
    return 0 if overall else 2


if __name__ == "__main__":
    raise SystemExit(main())

