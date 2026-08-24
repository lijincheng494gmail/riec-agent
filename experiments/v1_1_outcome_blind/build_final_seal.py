#!/usr/bin/env python3
"""Build final manifest and checksum ledger after validation."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "10_FINAL_FILE_MANIFEST.csv"
CHECKSUMS = ROOT / "11_FINAL_CHECKSUMS_SHA256.txt"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    files = sorted(
        path for path in ROOT.rglob("*")
        if path.is_file()
        and path not in {MANIFEST, CHECKSUMS}
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and path.name != ".DS_Store"
    )
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["relative_path", "sha256", "bytes"])
        for path in files:
            writer.writerow([path.relative_to(ROOT).as_posix(), digest(path), path.stat().st_size])
    with CHECKSUMS.open("w", encoding="utf-8") as handle:
        for path in files + [MANIFEST]:
            handle.write(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n")
    print(f"FINAL_MANIFEST_FILES={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

