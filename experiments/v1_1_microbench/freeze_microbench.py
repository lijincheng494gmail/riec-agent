#!/usr/bin/env python3
"""Seal the targeted cases, adjudicator and acceptance rules before formal execution."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "03_PREFREEZE_FILE_MANIFEST.csv"
CHECKSUMS = ROOT / "04_PREFREEZE_CHECKSUMS_SHA256.txt"
DECLARATION = ROOT / "05_PREFREEZE_DECLARATION.md"
GENERATED = {MANIFEST, CHECKSUMS, DECLARATION}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*")
        if path.is_file()
        and path not in GENERATED
        and "results" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and path.name not in {"11_FINAL_FILE_MANIFEST.csv", "12_FINAL_CHECKSUMS_SHA256.txt"}
    )


def main() -> int:
    files = source_files()
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["relative_path", "sha256", "bytes"])
        for path in files:
            writer.writerow([path.relative_to(ROOT).as_posix(), digest(path), path.stat().st_size])
    DECLARATION.write_text(
        f"""# Targeted microbenchmark prefreeze declaration

- `STATUS=TARGETED_CASES_AND_MUTANTS_PREFROZEN`
- `RULE_DESIGN_LEDGER_SHA256=7de7c487082a4d17d392999c6cf31e55129994b84af9c74b45c29bdc14e3d9a3`
- `EXECUTABLE_VALIDATION_LEDGER_SHA256=b5930b02f512bf1577b6ea47051b71c520bf49626f01cdb534a9814590aed694`
- `PREFREEZE_FILES={len(files)}`
- `PREFREEZE_MANIFEST_SHA256={digest(MANIFEST)}`
- `FORMAL_MICROBENCH_RUNS_ALLOWED=1`
- `MODEL_API_CALLS_ALLOWED=0`
- `OLD_LOCKBOX_ACCESS_ALLOWED=NO`

Any case, expectation, adjudication rule, mutant or acceptance-rule change requires a new microbenchmark version.
""",
        encoding="utf-8",
    )
    with CHECKSUMS.open("w", encoding="utf-8") as handle:
        for path in files + [MANIFEST, DECLARATION]:
            handle.write(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n")
    print("MICROBENCH_PREFREEZE=PASS")
    print(f"PREFREEZE_FILES={len(files)}")
    print(f"PREFREEZE_MANIFEST_SHA256={digest(MANIFEST)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

