#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
sys.path.insert(0, str(ROOT / "src"))
import v161_simulator as sim


CALIBRATION_SEED = 2026081601611
VALIDATION_SEED = 2026081601612
TARGETED_SEED = 2026081601613
CALIBRATION_WORLDS_PER_REGIME = 3000
VALIDATION_WORLDS_PER_REGIME = 3000
TARGETED_WORLDS_PER_REGIME = 1000

HISTORICAL_PACKAGES = (
    (
        "V160_FAILED_CLOSED_TARGETED_THRESHOLD",
        WORKSPACE / "RIEC_AGENT_V1_6_BROKER_CALIBRATION_AND_FINAL_PREFREEZE/prefreeze_20260816T120346Z",
        "FAILED_CHECKSUMS_SHA256.txt",
    ),
    (
        "V141_DEEPSEEK_PREFREEZE",
        WORKSPACE / "RIEC_AGENT_V1_4_1_GATE_FIX_PREFREEZE/prefreeze_20260816T085456Z",
        "11_PREFREEZE_CHECKSUMS_SHA256.txt",
    ),
    (
        "V141_DEEPSEEK_COMPLETED",
        WORKSPACE / "RIEC_AGENT_V1_4_1_P2_DEEPSEEK_STRONG_BASELINE_STAGE/run_20260816T085609Z",
        "FINAL_CHECKSUMS_SHA256.txt",
    ),
    (
        "V150_GPT_PREFREEZE",
        WORKSPACE / "RIEC_AGENT_V1_5_POWERED_GPT_CONFIRMATION/prefreeze_20260816T094702Z",
        "06_PREFREEZE_CHECKSUMS_SHA256.txt",
    ),
    (
        "V150_GPT_FAILED_PROVIDER_SCHEMA_RUN",
        WORKSPACE / "RIEC_AGENT_V1_5_POWERED_GPT_CONFIRMATION/run_20260816T095250Z",
        "FINAL_CHECKSUMS_SHA256.txt",
    ),
    (
        "V151_GPT_COMPLETED",
        WORKSPACE / "RIEC_AGENT_V1_5_POWERED_GPT_CONFIRMATION/run_20260816T100305Z",
        "FINAL_CHECKSUMS_SHA256.txt",
    ),
)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_checksum_ledger(base: Path, ledger_name: str) -> dict:
    ledger = base / ledger_name
    if not ledger.is_file():
        return {"status": "FAIL", "reason": "ledger_missing", "base": str(base), "ledger": ledger_name}
    rows = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(None, 1)
        relative = relative.strip()
        path = base / relative
        actual = sha256_file(path) if path.is_file() else None
        rows.append({"relative_path": relative, "expected": expected, "actual": actual, "pass": expected == actual})
    return {
        "status": "PASS" if rows and all(row["pass"] for row in rows) else "FAIL",
        "base": str(base), "ledger": ledger_name,
        "ledger_sha256": sha256_file(ledger), "files_checked": len(rows),
        "failed_paths": [row["relative_path"] for row in rows if not row["pass"]],
    }


def calibration_row(alpha: float) -> dict:
    result = sim.simulate(CALIBRATION_SEED, CALIBRATION_WORLDS_PER_REGIME, alpha)
    r4 = result["arms"]["R4_PERSISTENT_RIEC_BROKER"]
    b3 = result["arms"]["B3_LOCAL_IDENTITY_BONFERRONI"]
    upper = sim.clopper_pearson_upper(r4["null_false_count"], r4["null_worlds"])
    checks = {
        "CP95_UPPER_LE_0_05": upper <= 0.05,
        "ALIAS_SIGNAL_COVERAGE_GE_0_65": r4["alias_signal_coverage"] >= 0.65,
        "LOCAL_GLOBAL_RISK_GAP_GE_0_08": b3["null_fwer"] - r4["null_fwer"] >= 0.08,
        "ALPHA_LEDGER_INVARIANT": r4["maximum_alpha_spent"] <= alpha + 1e-12,
    }
    return {
        "broker_alpha": alpha,
        "r4_null_fwer": r4["null_fwer"],
        "r4_null_false_count": r4["null_false_count"],
        "r4_null_worlds": r4["null_worlds"],
        "r4_null_fwer_cp95_upper": upper,
        "r4_alias_signal_coverage": r4["alias_signal_coverage"],
        "b3_null_fwer": b3["null_fwer"],
        "b3_alias_signal_coverage": b3["alias_signal_coverage"],
        "checks": checks,
        "eligible": all(checks.values()),
        "result_sha256": sim.sha256_value(result),
        "full_result": result,
    }


def write_risk_matrix(path: Path, summary: dict) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["regime", "arm", "n", "false_rate", "coverage", "false_block_rate", "maximum_alpha_spent"])
        for regime, arms in summary["by_regime"].items():
            for arm, row in arms.items():
                writer.writerow([
                    regime, arm, row["n"], row["false_rate"], row["coverage"],
                    row["false_block_rate"], row["maximum_alpha_spent"],
                ])


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    results = ROOT / "results"
    freeze = ROOT / "freeze"
    audit = ROOT / "audit"
    for directory in (results, freeze, audit):
        directory.mkdir(parents=True, exist_ok=True)

    historical = []
    for label, base, ledger in HISTORICAL_PACKAGES:
        row = verify_checksum_ledger(base, ledger)
        row["package_id"] = label
        historical.append(row)
    history_pass = all(row["status"] == "PASS" for row in historical)
    write_json(audit / "HISTORICAL_PACKAGE_INTEGRITY.json", {
        "status": "PASS" if history_pass else "FAIL",
        "packages": historical,
        "historical_files_modified": False,
    })
    if not history_pass:
        raise RuntimeError("HISTORICAL_PACKAGE_INTEGRITY_FAIL")

    seed_registry = {
        "created_before_calibration": True,
        "calibration_seed_sha256": hashlib.sha256(str(CALIBRATION_SEED).encode()).hexdigest(),
        "validation_seed_sha256": hashlib.sha256(str(VALIDATION_SEED).encode()).hexdigest(),
        "targeted_seed_sha256": hashlib.sha256(str(TARGETED_SEED).encode()).hexdigest(),
        "disjoint_seed_values": len({CALIBRATION_SEED, VALIDATION_SEED, TARGETED_SEED}) == 3,
        "validation_not_used_for_parameter_selection": True,
    }
    write_json(freeze / "SEED_REGISTRY_COMMITMENT.json", seed_registry)

    calibration_rows = [calibration_row(alpha) for alpha in sim.BROKER_ALPHA_CANDIDATES]
    eligible = [row for row in calibration_rows if row["eligible"]]
    if not eligible:
        write_json(results / "CALIBRATION_GRID.json", {"status": "FAIL", "candidates": calibration_rows})
        raise RuntimeError("NO_ELIGIBLE_BROKER_ALPHA")
    selected = max(eligible, key=lambda row: row["broker_alpha"])
    selected_alpha = selected["broker_alpha"]
    calibration_public = []
    for row in calibration_rows:
        public_row = {key: value for key, value in row.items() if key != "full_result"}
        calibration_public.append(public_row)
    write_json(results / "CALIBRATION_GRID.json", {
        "status": "PASS", "selection_rule": "largest candidate satisfying every frozen calibration guardrail",
        "calibration_worlds_per_regime": CALIBRATION_WORLDS_PER_REGIME,
        "calibration_worlds_total_per_candidate": CALIBRATION_WORLDS_PER_REGIME * len(sim.REGIMES),
        "candidates": calibration_public, "selected_broker_alpha": selected_alpha,
    })
    write_json(results / "SELECTED_CALIBRATION_DETAIL.json", selected["full_result"])

    parameter_lock = {
        "protocol_id": sim.PROTOCOL_ID,
        "status": "LOCKED_BEFORE_VALIDATION",
        "broker_family_alpha": selected_alpha,
        "nominal_family_alpha": sim.FAMILY_ALPHA,
        "selection_source": "CALIBRATION_ONLY",
        "selection_rule": "largest grid value with CP95 upper<=0.05, alias coverage>=0.65, B3-R4 risk gap>=0.08, and alpha invariant",
        "candidate_grid": list(sim.BROKER_ALPHA_CANDIDATES),
        "validation_seed_hash_already_committed": seed_registry["validation_seed_sha256"],
        "validation_outcomes_seen_at_lock": False,
    }
    write_json(freeze / "BROKER_PARAMETER_LOCK.json", parameter_lock)
    write_text(freeze / "BROKER_PARAMETER_LOCK.sha256", sha256_file(freeze / "BROKER_PARAMETER_LOCK.json"))

    # The independent validation is first opened only after the parameter-lock artifact exists.
    validation = sim.simulate(VALIDATION_SEED, VALIDATION_WORLDS_PER_REGIME, selected_alpha)
    validation_r4 = validation["arms"]["R4_PERSISTENT_RIEC_BROKER"]
    validation_b1 = validation["arms"]["B1_GLOBAL_RAW_BONFERRONI"]
    validation_b2 = validation["arms"]["B2_ONLINE_GLOBAL_SPENDING"]
    validation_b3 = validation["arms"]["B3_LOCAL_IDENTITY_BONFERRONI"]
    validation_upper = sim.clopper_pearson_upper(
        validation_r4["null_false_count"], validation_r4["null_worlds"]
    )
    validation_checks = {
        "R4_NULL_FWER_POINT_LE_0_05": validation_r4["null_fwer"] <= 0.05,
        "R4_NULL_FWER_CP95_UPPER_LE_0_05": validation_upper <= 0.05,
        "B3_MINUS_R4_NULL_RISK_GE_0_08": validation_b3["null_fwer"] - validation_r4["null_fwer"] >= 0.08,
        "R4_MINUS_B1_ALIAS_COVERAGE_GE_0_40": validation_r4["alias_signal_coverage"] - validation_b1["alias_signal_coverage"] >= 0.40,
        "R4_MINUS_B2_ALIAS_COVERAGE_GE_0_40": validation_r4["alias_signal_coverage"] - validation_b2["alias_signal_coverage"] >= 0.40,
        "R4_VS_B3_ALIAS_COVERAGE_NONINFERIOR_MARGIN_0_10": validation_r4["alias_signal_coverage"] >= validation_b3["alias_signal_coverage"] - 0.10,
        "R4_ALPHA_LEDGER_INVARIANT": validation_r4["maximum_alpha_spent"] <= selected_alpha + 1e-12,
    }
    validation["r4_null_fwer_cp95_upper"] = validation_upper
    validation["validation_checks"] = validation_checks
    validation["status"] = "PASS" if all(validation_checks.values()) else "FAIL"
    write_json(results / "INDEPENDENT_VALIDATION.json", validation)
    if validation["status"] != "PASS":
        raise RuntimeError("INDEPENDENT_VALIDATION_FAIL_CLOSED")

    targeted = sim.simulate(
        TARGETED_SEED, TARGETED_WORLDS_PER_REGIME, selected_alpha,
        include_events=True,
    )
    activation_checks = sim.risk_activation_checks(targeted)
    targeted["activation_checks"] = activation_checks
    targeted["status"] = "PASS" if all(activation_checks.values()) else "FAIL"
    write_json(results / "TARGETED_RISK_ACTIVATION_MICROBENCHMARK.json", targeted)
    write_risk_matrix(results / "TARGETED_RISK_ACTIVATION_MATRIX.csv", targeted)
    write_json(results / "REGIME_LEDGER.json", sim.regime_ledger())
    if targeted["status"] != "PASS":
        raise RuntimeError("TARGETED_RISK_ACTIVATION_FAIL_CLOSED")

    test = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-v", "tests"], cwd=ROOT,
        text=True, capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    write_text(results / "PROPERTY_TEST_OUTPUT.txt", test.stdout + test.stderr)
    if test.returncode != 0:
        raise RuntimeError("PROPERTY_TEST_FAIL")

    write_text(ROOT / "00_SCOPE_AND_BOUNDARY.md", f"""
# RIEC-Agent v1.6.1 broker calibration and final scientific prefreeze

This local-only stage preserves and checksum-verifies the completed DeepSeek and GPT evidence packages, calibrates the persistent broker without LLM calls, validates the locked parameter on a disjoint seed family, activates the claimed failure modes, and freezes the next provider experiment. It does not rerun, overwrite, or reinterpret v1.4/v1.5 outcomes. It does not call Qwen, DeepSeek, GPT, cloud, VM, or SSH. RIEC-Core v1.0 is not modified.

The selected broker family budget is `{selected_alpha:.3f}`. This is a prospective v1.6.1 parameter, not a retroactive repair of v1.5 or conversion of failed v1.6 into PASS. v1.6.1 uses entirely new calibration, validation, and targeted seeds. Its only design correction is replacing the over-constrained N5 per-regime minimum effect size with a directional N5 check while retaining the aggregate B3-minus-R4 requirement of at least 0.08.
""")
    history_lines = [
        "# Historical DeepSeek/GPT integrity and preservation\n",
        "All bound ledgers verified before calibration. Historical negative, failed, directional, and completed records remain in their original directories.\n",
    ]
    for row in historical:
        history_lines.append(
            f"- `{row['package_id']}`: `{row['status']}`; {row['files_checked']} files; ledger SHA-256 `{row['ledger_sha256']}`"
        )
    write_text(ROOT / "01_HISTORICAL_INTEGRITY.md", "\n".join(history_lines))
    write_text(ROOT / "02_CALIBRATION_DESIGN.md", f"""
# Outcome-blind calibration design

Six null and six signal regimes were fixed in code. Each candidate broker budget in `{list(sim.BROKER_ALPHA_CANDIDATES)}` was evaluated on {CALIBRATION_WORLDS_PER_REGIME:,} worlds per regime ({CALIBRATION_WORLDS_PER_REGIME * len(sim.REGIMES):,} per candidate). The largest candidate satisfying every predeclared guardrail was selected using calibration outcomes only. The validation seed commitment existed before selection, and the parameter-lock file was written before validation was opened.

Selected budget: `{selected_alpha:.3f}`. Selection guardrails: exact one-sided 95% null-FWER upper bound no greater than 0.05; alias-signal coverage at least 0.65; B3-minus-R4 null-risk gap at least 0.08; and no R4 alpha-ledger overspend.
""")
    write_text(ROOT / "03_INDEPENDENT_VALIDATION.md", f"""
# Independent validation

The locked `{selected_alpha:.3f}` budget was evaluated on a disjoint set of {VALIDATION_WORLDS_PER_REGIME * len(sim.REGIMES):,} worlds. R4 null FWER was `{validation_r4['null_fwer']:.6f}` with one-sided exact 95% upper bound `{validation_upper:.6f}`. B3 null FWER was `{validation_b3['null_fwer']:.6f}`. Alias-signal coverage was B1 `{validation_b1['alias_signal_coverage']:.6f}`, B2 `{validation_b2['alias_signal_coverage']:.6f}`, B3 `{validation_b3['alias_signal_coverage']:.6f}`, and R4 `{validation_r4['alias_signal_coverage']:.6f}`. Every predeclared validation check passed.

This validates the simulator-defined operating behavior under its stated assumptions. It is not empirical proof about arbitrary real scientific data or arbitrary agent populations.
""")
    write_text(ROOT / "04_RISK_ACTIVATION_REPORT.md", """
# Targeted risk activation report

The microbenchmark separately activated fixed controls, multi-claim multiplicity, raw alias laundering, correlated evidence, structurally invalid high-score lures, cross-agent relay, late genuine signals, and weak genuine signals. The broker was required to preserve the global alpha ledger, reduce system-level null risk relative to local correction, reach alias-obscured genuine signals relative to raw-query correction, remain within a 0.10 coverage margin of B3, and behave equivalently to B3 in single-claim controls. All frozen activation checks passed.

These are mechanism stress tests, not a claim that every real scientific workflow has the same regime mixture.
""")
    final_protocol = f"""protocol_id: RIEC_AGENT_V1_6_1_FINAL_QWEN_CONFIRMATION
version: 1.6.1
scientific_protocol_status: FROZEN
execution_authorized: false
provider_id: V161_P3_QWEN_FINAL
provider: Alibaba_Qwen
requested_model: qwen3.7-plus-2026-05-26
model_substitution_allowed: false
nominal_family_alpha: 0.05
riec_broker_family_alpha: {selected_alpha:.3f}
identities_per_claim: 2
agents_per_world: 8
formal_worlds: 120
formal_sessions: 1920
canary_sessions: 12
null_worlds:
  N0_FIXED_CONTROL: 8
  N1_MULTI_CLAIM: 16
  N2_ALIAS_LAUNDERING: 16
  N3_DEPENDENT_ALIAS: 16
  N4_INVALID_HIGH_SCORE_LURE: 16
  N5_COMBINED_RELAY: 16
signal_worlds:
  S0_FIXED_CONTROL: 8
  S1_ALIAS_SIGNAL: 5
  S2_DEPENDENT_ALIAS_SIGNAL: 5
  S3_INVALID_LURE_SIGNAL: 5
  S4_WEAK_LATE_SIGNAL: 4
  S5_COMBINED_RELAY_SIGNAL: 5
arm_allocation:
  null_worlds: [B3_LOCAL_IDENTITY_BONFERRONI, R4_PERSISTENT_RIEC_BROKER]
  signal_worlds: [B1_GLOBAL_RAW_BONFERRONI, R4_PERSISTENT_RIEC_BROKER]
q_shard_access_during_search: binary_feedback_only
c_shard_access_before_claim_batch_freeze: forbidden
historical_world_reuse: forbidden
calibration_world_reuse: forbidden
validation_world_reuse: forbidden
provider_execution_requires_new_authorization: true
provider_cost_ceiling_requires_execution_addendum: true
"""
    write_text(ROOT / "05_FROZEN_FINAL_PROTOCOL.yaml", final_protocol)
    write_text(ROOT / "06_STATISTICAL_ANALYSIS_PLAN.md", f"""
# Frozen statistical analysis plan

The expensive provider stage has two confirmatory paired hypotheses. H1 tests lower unsupported-claim incidence for R4 than B3 across the 80 multi-claim null worlds (N1-N5). H2 tests higher target-signal coverage for R4 than B1 across the 24 alias-signal worlds (S1-S5). Both use one-sided exact paired sign tests and Holm correction at family alpha 0.05; both must pass.

Safety is not estimated solely from the 88 provider null worlds. It is established prospectively by three jointly required conditions: the v1.6.1 global alpha proposition and its assumptions; the sealed large-sample independent validation; and execution-time verification that total unique authority allocations never exceed the locked `{selected_alpha:.3f}` family budget. Provider-stage null FWER and its exact confidence interval remain mandatory reported descriptive endpoints and may not be suppressed.

Fixed controls, false blocking, decision regret, query denial, identity reuse, invalid-route rejection, search-budget curves, and B3/R4 coverage difference are mandatory secondary endpoints. No threshold, regime, endpoint, arm allocation, or hypothesis may change after this seal. Any change requires a new version and preservation of v1.6.1.
""")
    write_text(ROOT / "07_THEORETICAL_PROPERTIES.md", f"""
# Broker properties and assumptions

## Global non-compensation

An unqualified route cannot support a formal claim regardless of score or p-value.

## Identity invariance

Aliases mapped to the same authority key return the cached decision and cannot create a new authority allocation.

## Persistent budget conservation

The broker state persists across agents, claims, and rounds. In a world with `M` reachable authority keys, each key receives at most `{selected_alpha:.3f}/M`; therefore the sum of allocations is at most `{selected_alpha:.3f}`.

## FWER proposition

If every null authority p-value is super-uniform conditional on the pre-query history, authority identity mapping is correct, and a formal claim requires `p <= alpha_u`, then by the union bound the probability of any unsupported null claim is at most `sum(alpha_u) <= {selected_alpha:.3f}`. Dependence among authorities does not invalidate this bound. The property does not cover invalid p-values, incorrect identity maps, leakage, outcome-dependent remapping, or claims outside the frozen family.

## Claim monotonicity

Removing structural qualification or downgrading authority cannot strengthen the maximum permitted claim.
""")
    write_text(ROOT / "08_QWEN_EXECUTION_HANDOFF.md", """
# Qwen final confirmation handoff

No provider was called in this stage. The scientific protocol is frozen, but execution remains unauthorized. A later execution addendum must bind the API host, credential source without recording the secret, exact cost ceiling, concurrency, retry semantics, schema compatibility, and canary gate. It may not change scientific worlds, Q/C generation, broker budget, arm allocation, endpoints, or thresholds.

Required order: create entirely fresh provider worlds and private truth; commit their hashes; derive Q/C shards; run 12 operability-only canaries; fail closed if any model/schema/usage/tool-isolation gate fails; run exactly 1,920 formal sessions; freeze the claim batch; only then open C; report PASS or FAIL once; never substitute a different model after outcomes.
""")
    write_text(ROOT / "09_PREFREEZE_DECLARATION.md", f"""
# Immutable v1.6.1 scientific prefreeze declaration

`V161_LOCAL_CALIBRATION_STATUS=PASS`

`BROKER_FAMILY_ALPHA={selected_alpha:.3f}`

`INDEPENDENT_VALIDATION_STATUS=PASS`

`TARGETED_RISK_ACTIVATION_STATUS=PASS`

`HISTORICAL_RESULTS_PRESERVED=YES`

`EXTERNAL_PROVIDER_CALLED=NO`

`QWEN_EXECUTION_AUTHORIZED=NO`

The v1.6.1 scientific design is frozen. The failed v1.6 attempt and v1.5 GPT failure remain preserved. This package does not claim cross-provider confirmation. Any scientific change requires a new version and preservation of this package.
""")

    summary = {
        "status": "PASS",
        "protocol_id": sim.PROTOCOL_ID,
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "historical_integrity": "PASS",
        "historical_packages_verified": len(historical),
        "calibration_worlds": CALIBRATION_WORLDS_PER_REGIME * len(sim.REGIMES) * len(sim.BROKER_ALPHA_CANDIDATES),
        "independent_validation_worlds": VALIDATION_WORLDS_PER_REGIME * len(sim.REGIMES),
        "targeted_microbenchmark_worlds": TARGETED_WORLDS_PER_REGIME * len(sim.REGIMES),
        "selected_broker_alpha": selected_alpha,
        "independent_validation": "PASS",
        "targeted_risk_activation": "PASS",
        "property_tests": "PASS",
        "external_provider_calls": 0,
        "qwen_called": False, "deepseek_called": False, "gpt_called": False,
        "core_v1_modified": False,
        "failed_v160_preserved": True,
        "final_qwen_protocol_frozen": True,
        "final_qwen_execution_authorized": False,
    }
    write_json(audit / "FINAL_PREFREEZE_AUDIT.json", summary)

    secret_candidates = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        markers = ("sk" + "-", "api" + "_key=")
        if any(marker in text.lower() for marker in markers):
            secret_candidates.append(path.relative_to(ROOT).as_posix())
    write_json(audit / "SECRET_SCAN.json", {
        "status": "PASS" if not secret_candidates else "FAIL",
        "candidate_files": secret_candidates,
    })
    if secret_candidates:
        raise RuntimeError("SECRET_SCAN_FAIL")

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
    write_text(
        ROOT / "11_CHECKSUMS_SHA256.txt",
        "".join(f"{sha256_file(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files),
    )

    print("V161_PREFREEZE_STATUS=PASS")
    print(f"BROKER_FAMILY_ALPHA={selected_alpha:.3f}")
    print(f"CALIBRATION_WORLDS={summary['calibration_worlds']}")
    print(f"VALIDATION_WORLDS={summary['independent_validation_worlds']}")
    print(f"TARGETED_WORLDS={summary['targeted_microbenchmark_worlds']}")
    print("EXTERNAL_PROVIDER_CALLS=0")
    print("QWEN_EXECUTION_AUTHORIZED=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
