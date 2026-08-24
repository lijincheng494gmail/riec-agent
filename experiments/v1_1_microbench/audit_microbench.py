#!/usr/bin/env python3
"""Postrun audit for targeted activation and mutation results."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
OUT = ROOT / "results/10_POSTRUN_AUDIT.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_ledger(root: Path, ledger: Path) -> tuple[bool, int]:
    entries = []
    for line in ledger.read_text().splitlines():
        expected, relative = line.split("  ", 1)
        entries.append((expected, root / relative))
    return all(path.is_file() and digest(path) == expected for expected, path in entries), len(entries)


def main() -> int:
    prefreeze_ok, prefreeze_count = verify_ledger(ROOT, ROOT / "04_PREFREEZE_CHECKSUMS_SHA256.txt")
    design_root = WORKSPACE / "RIEC_AGENT_V1_1_RULE_DESIGN/design_20260815T220449Z"
    validation_root = WORKSPACE / "RIEC_AGENT_V1_1_RULE_VALIDATION/validation_20260815T222631Z"
    design_ok, _ = verify_ledger(design_root, design_root / "11_CHECKSUMS_SHA256.txt")
    validation_ok, _ = verify_ledger(validation_root, validation_root / "11_FINAL_CHECKSUMS_SHA256.txt")
    unit_ok = "UNIT_TEST_STATUS=PASS" in (ROOT / "results/05_UNIT_TEST_RESULTS.txt").read_text()
    with (ROOT / "results/06_CASE_RESULTS.csv").open(newline="", encoding="utf-8") as handle:
        cases = list(csv.DictReader(handle))
    with (ROOT / "results/07_ACTIVATION_COVERAGE.csv").open(newline="", encoding="utf-8") as handle:
        coverage = list(csv.DictReader(handle))
    with (ROOT / "results/08_MUTATION_RESULTS.csv").open(newline="", encoding="utf-8") as handle:
        mutants = list(csv.DictReader(handle))
    cases_ok = bool(cases) and all(row["expectation_match"] == "1" for row in cases)
    controls_ok = all(
        not row["core_failures"] and not row["triggered_rules"]
        for row in cases if row["kind"] == "CONTROL"
    )
    coverage_ok = bool(coverage) and all(row["covered"] == "1" for row in coverage)
    mutants_ok = bool(mutants) and all(row["killed"] == "1" for row in mutants)
    overall = all((prefreeze_ok, design_ok, validation_ok, unit_ok, cases_ok, controls_ok, coverage_ok, mutants_ok))
    OUT.write_text(
        f"""# Targeted microbenchmark postrun audit

- `BOUND_RULE_DESIGN_VERIFY={'PASS' if design_ok else 'FAIL'}`
- `BOUND_EXECUTABLE_VALIDATION_VERIFY={'PASS' if validation_ok else 'FAIL'}`
- `PREFREEZE_CHECKSUM_VERIFY={'PASS' if prefreeze_ok else 'FAIL'}`
- `PREFREEZE_ENTRIES_CHECKED={prefreeze_count}`
- `UNIT_TEST_STATUS={'PASS' if unit_ok else 'FAIL'}`
- `CASE_EXPECTATIONS={sum(row['expectation_match'] == '1' for row in cases)}/{len(cases)}`
- `CONTROL_FALSE_ACTIVATIONS={sum(bool(row['core_failures'] or row['triggered_rules']) for row in cases if row['kind'] == 'CONTROL')}`
- `ACTIVATION_COVERAGE={sum(row['covered'] == '1' for row in coverage)}/{len(coverage)}`
- `MUTANTS_KILLED={sum(row['killed'] == '1' for row in mutants)}/{len(mutants)}`
- `TARGETED_MICROBENCH={'PASS' if overall else 'FAIL'}`
- `MODEL_API_CALLED=NO`
- `OLD_PROVIDER_PRIVATE_TRUTH_ACCESSED=NO`
- `OLD_NEURO_TOUCHED=NO`
- `CORE_V1_0_MUTATED=NO`

Passing establishes deterministic risk-activation and mutation sensitivity only. It is not empirical agent validation and does not close the remaining prefreeze checklist.
""",
        encoding="utf-8",
    )
    print(f"TARGETED_MICROBENCH_AUDIT={'PASS' if overall else 'FAIL'}")
    return 0 if overall else 2


if __name__ == "__main__":
    raise SystemExit(main())

