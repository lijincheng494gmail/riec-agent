#!/usr/bin/env python3
"""Build the deterministic manifest and checksum ledger for this design package."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "10_FILE_MANIFEST.csv"
CHECKSUMS = ROOT / "11_CHECKSUMS_SHA256.txt"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    files = sorted(
        path
        for path in ROOT.iterdir()
        if path.is_file() and path not in {MANIFEST, CHECKSUMS} and path.name != ".DS_Store"
    )
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["relative_path", "sha256", "bytes"])
        for path in files:
            writer.writerow([path.name, digest(path), path.stat().st_size])
    with CHECKSUMS.open("w", encoding="utf-8") as handle:
        for path in files + [MANIFEST]:
            handle.write(f"{digest(path)}  {path.name}\n")
    print(f"DESIGN_FILES={len(files)}")
    print(f"MANIFEST={MANIFEST}")
    print(f"CHECKSUMS={CHECKSUMS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

