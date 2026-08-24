#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "audit"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


attempt = AUDIT / "SECRET_SCAN.json"
if attempt.is_file() and not (AUDIT / "SECRET_SCAN_ATTEMPT1_FAILED.json").exists():
    shutil.copy2(attempt, AUDIT / "SECRET_SCAN_ATTEMPT1_FAILED.json")

markers = ("sk" + "-", "api" + "_key=")
candidates = []
for path in ROOT.rglob("*"):
    if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
        continue
    if path.name in {"10_MANIFEST.csv", "11_CHECKSUMS_SHA256.txt"}:
        continue
    content = path.read_text(encoding="utf-8", errors="ignore").lower()
    if any(marker in content for marker in markers):
        candidates.append(path.relative_to(ROOT).as_posix())
write_json(AUDIT / "SECRET_SCAN.json", {
    "status": "PASS" if not candidates else "FAIL",
    "candidate_files": candidates,
    "repair_scope": "scanner_self-match_only",
    "scientific_outputs_rerun": False,
})
if candidates:
    raise RuntimeError("SECRET_SCAN_REPAIR_FAIL")

final_audit_path = AUDIT / "FINAL_PREFREEZE_AUDIT.json"
final_audit = json.loads(final_audit_path.read_text(encoding="utf-8"))
final_audit["execution_repairs"] = [{
    "repair": "secret_scanner_self_match_removed",
    "scientific_change": False,
    "scientific_outputs_rerun": False,
    "attempt1_preserved": True,
}]
final_audit["finalized_utc"] = datetime.now(timezone.utc).isoformat()
write_json(final_audit_path, final_audit)

excluded = {ROOT / "10_MANIFEST.csv", ROOT / "11_CHECKSUMS_SHA256.txt"}
files = sorted(
    path for path in ROOT.rglob("*") if path.is_file() and path not in excluded
    and "__pycache__" not in path.parts and not path.name.endswith(".pyc")
)
with (ROOT / "10_MANIFEST.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["relative_path", "bytes", "sha256"])
    for path in files:
        writer.writerow([path.relative_to(ROOT).as_posix(), path.stat().st_size, sha256_file(path)])
files.append(ROOT / "10_MANIFEST.csv")
(ROOT / "11_CHECKSUMS_SHA256.txt").write_text(
    "".join(f"{sha256_file(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files),
    encoding="utf-8",
)
print("V161_FINALIZATION_STATUS=PASS")
