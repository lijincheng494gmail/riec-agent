#!/usr/bin/env python3
"""Seal validation code and protocol before formal simulation execution."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "02_PREFREEZE_FILE_MANIFEST.csv"
CHECKSUMS = ROOT / "03_PREFREEZE_CHECKSUMS_SHA256.txt"
DECLARATION = ROOT / "04_PREFREEZE_DECLARATION.md"
GENERATED = {MANIFEST, CHECKSUMS, DECLARATION}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_files() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*")
        if path.is_file()
        and path not in GENERATED
        and "results" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and path.name not in {"10_FINAL_FILE_MANIFEST.csv", "11_FINAL_CHECKSUMS_SHA256.txt"}
    )


def main() -> int:
    files = source_files()
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["relative_path", "sha256", "bytes"])
        for path in files:
            writer.writerow([path.relative_to(ROOT).as_posix(), digest(path), path.stat().st_size])
    declaration = f"""# Validation prefreeze declaration

- `STATUS=VALIDATION_CODE_AND_SIMULATION_PROTOCOL_PREFROZEN`
- `DESIGN_LEDGER_SHA256=7de7c487082a4d17d392999c6cf31e55129994b84af9c74b45c29bdc14e3d9a3`
- `PREFREEZE_FILES={len(files)}`
- `PREFREEZE_MANIFEST_SHA256={digest(MANIFEST)}`
- `FORMAL_SIMULATION_RUNS_ALLOWED=1`
- `MODEL_API_CALLS_ALLOWED=0`
- `OLD_NEURO_ACCESS_ALLOWED=NO`

Any source, test, protocol, seed or acceptance-rule change after this declaration requires a new validation directory and a new prefreeze seal.
"""
    DECLARATION.write_text(declaration, encoding="utf-8")
    with CHECKSUMS.open("w", encoding="utf-8") as handle:
        for path in files + [MANIFEST, DECLARATION]:
            handle.write(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n")
    print("VALIDATION_PREFREEZE=PASS")
    print(f"PREFREEZE_FILES={len(files)}")
    print(f"PREFREEZE_MANIFEST_SHA256={digest(MANIFEST)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

