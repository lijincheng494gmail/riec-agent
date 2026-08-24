from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


OUT = Path(__file__).resolve().parent
PACKAGE_ROOT = OUT.parents[1]
SOURCE = PACKAGE_ROOT / "provider/qwen_v1_6_1"
ANALYSIS = OUT / "analysis"
AUDIT = OUT / "audit"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_protocol():
    path = SOURCE / "src/qwen_protocol.py"
    spec = importlib.util.spec_from_file_location("qwen_protocol_frozen", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen protocol")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    protocol = load_protocol()

    source_inputs = {
        "formal_world_registry": SOURCE / "public/FORMAL_WORLD_REGISTRY.json",
        "formal_schedule": SOURCE / "public/FORMAL_SCHEDULE.json",
        "formal_session_ledger": SOURCE / "sessions/FORMAL_SESSION_LEDGER.json",
        "claim_batch_ledger": SOURCE / "audit/CLAIM_BATCH_LEDGER.json",
        "claim_batch_freeze_gate": SOURCE / "audit/CLAIM_BATCH_FREEZE_GATE.json",
        "c_shard": SOURCE / "lockbox/C_SHARD.json",
        "frozen_protocol": SOURCE / "src/qwen_protocol.py",
        "original_final_status": SOURCE / "FINAL_STATUS.txt",
    }
    source_hashes = {name: sha256(path) for name, path in source_inputs.items()}
    write_json(AUDIT / "SOURCE_INTEGRITY.json", {
        "source_run": str(SOURCE),
        "source_files_sha256": source_hashes,
        "source_run_modified": False,
    })

    worlds = read_json(source_inputs["formal_world_registry"])
    schedule = read_json(source_inputs["formal_schedule"])
    records = read_json(source_inputs["formal_session_ledger"])
    world_map = {world["world_id"]: world for world in worlds}
    missing = [record for record in records if not record.get("accepted")]
    accepted = [record for record in records if record.get("accepted")]
    affected_worlds = sorted({record["world_id"] for record in missing})

    missing_rows = []
    for record in missing:
        attempts = record.get("attempts") or []
        missing_rows.append({
            "session_id": record["session_id"],
            "world_id": record["world_id"],
            "truth_class": world_map[record["world_id"]]["truth_class_public"],
            "risk_regime": world_map[record["world_id"]]["risk_regime"],
            "arm": record["arm"],
            "agent_index": record["agent_index"],
            "claim": record["claim"],
            "terminal_disposition": record.get("terminal_disposition"),
            "attempt_count": record.get("attempt_count"),
            "input_tokens": record.get("usage", {}).get("input_tokens", 0),
            "output_tokens": record.get("usage", {}).get("output_tokens", 0),
            "response_present": bool(record.get("ranked_candidate_ids")),
            "attempt_detail_present": bool(attempts),
        })
    write_json(AUDIT / "TRANSPORT_MISSING_LEDGER.json", missing_rows)

    all_transport_only = all(
        row["terminal_disposition"] == "TRANSPORT_FAILURE"
        and row["input_tokens"] == 0
        and row["output_tokens"] == 0
        and not row["response_present"]
        for row in missing_rows
    )
    if len(records) != len(schedule) or len(missing) != 8 or not all_transport_only:
        raise RuntimeError("adjudication precondition failed")

    decision_text = f"""# Qwen available-case adjudication decision

The original v1.6.1 confirmatory run remains permanently recorded as `FAIL_CLOSED_BEFORE_C` under its frozen all-sessions-complete gate.

Following explicit user adjudication on 2026-08-16, the eight zero-token, zero-response `TRANSPORT_FAILURE` records are treated as operational missingness. They are retained and are not converted into model answers, behavioral failures, or successful sessions. No session is rerun. The remaining 1,912 accepted sessions are scored as an available-case analysis.

Because this decision was made after the technical failure, the resulting analysis is labelled `POST_FAILURE_USER_AUTHORIZED_AVAILABLE_CASE`, not a pristine prospective confirmation. A complete-world sensitivity analysis excludes every world touched by a missing session. An extreme H1 sensitivity bound additionally assigns all six affected worlds in the direction least favorable to R4.

Original source run: `{SOURCE}`
Original source run modified: `NO`
Accepted sessions: `{len(accepted)}`
Transport-missing sessions: `{len(missing)}`
Affected worlds: `{len(affected_worlds)}`
"""
    (OUT / "00_ADJUDICATION_DECISION.md").write_text(decision_text, encoding="utf-8")

    states = {}
    for world in worlds:
        arms = protocol.NULL_ARMS if world["truth_class_public"] == "NULL" else protocol.SIGNAL_ARMS
        for arm in arms:
            path = SOURCE / "broker_state" / f"{world['world_id']}__{arm}.json"
            if not path.is_file():
                raise RuntimeError(f"missing broker state: {path}")
            states[(world["world_id"], arm)] = read_json(path)

    alpha_ok = all(
        state["alpha_spent"] <= protocol.BROKER_ALPHA + 1e-12
        for (world_id, arm), state in states.items()
        if arm == "R4_PERSISTENT_RIEC_BROKER"
    )
    claim_hash = sha256(source_inputs["claim_batch_ledger"])
    write_json(AUDIT / "C_OPEN_EVENT.json", {
        "opened_utc": datetime.now(timezone.utc).isoformat(),
        "authorization": "<SOURCE_RUN_EXPLICIT_USER_AUTHORIZATION_REDACTED>",
        "source_claim_batch_sha256": claim_hash,
        "accepted_sessions": len(accepted),
        "transport_missing_sessions": len(missing),
        "affected_worlds": affected_worlds,
        "analysis_authority": "POST_FAILURE_USER_AUTHORIZED_AVAILABLE_CASE",
    })
    c_truth = read_json(source_inputs["c_shard"])

    missing_by_key: dict[tuple[str, str], list[str]] = {}
    for record in missing:
        missing_by_key.setdefault((record["world_id"], record["arm"]), []).append(record["session_id"])

    world_rows = []
    for world in worlds:
        arms = protocol.NULL_ARMS if world["truth_class_public"] == "NULL" else protocol.SIGNAL_ARMS
        for arm in arms:
            state = states[(world["world_id"], arm)]
            score = protocol.score_state(state, c_truth[world["world_id"]])
            missing_ids = missing_by_key.get((world["world_id"], arm), [])
            world_rows.append({
                "world_id": world["world_id"],
                "risk_regime": world["risk_regime"],
                "truth_class": world["truth_class_public"],
                "arm": arm,
                "planned_sessions": protocol.AGENTS_PER_WORLD,
                "observed_sessions": len(state["events"]),
                "transport_missing_sessions": missing_ids,
                "complete_arm": not missing_ids,
                **score,
            })
    write_json(ANALYSIS / "WORLD_ARM_AVAILABLE_CASE_LEDGER.json", world_rows)
    by = {(row["world_id"], row["arm"]): row for row in world_rows}

    def rate(selected_worlds, arm, truth, endpoint, exclude_control=False):
        ids = {world["world_id"] for world in selected_worlds}
        subset = [
            row for row in world_rows
            if row["world_id"] in ids and row["arm"] == arm and row["truth_class"] == truth
        ]
        if exclude_control:
            subset = [row for row in subset if row["risk_regime"] not in {"N0_FIXED_CONTROL", "S0_FIXED_CONTROL"}]
        return {
            "numerator": sum(bool(row[endpoint]) for row in subset),
            "denominator": len(subset),
            "rate": sum(bool(row[endpoint]) for row in subset) / len(subset) if subset else None,
        }

    def evaluate(selected_worlds, label):
        h1_fav = h1_adv = h2_fav = h2_adv = 0
        for world in selected_worlds:
            wid = world["world_id"]
            if world["truth_class_public"] == "NULL" and world["risk_regime"] != "N0_FIXED_CONTROL":
                b3 = by[(wid, "B3_LOCAL_IDENTITY_BONFERRONI")]["unsupported"]
                r4 = by[(wid, "R4_PERSISTENT_RIEC_BROKER")]["unsupported"]
                h1_fav += int(b3 and not r4)
                h1_adv += int(r4 and not b3)
            if world["truth_class_public"] == "SIGNAL" and world["risk_regime"] != "S0_FIXED_CONTROL":
                b1 = by[(wid, "B1_GLOBAL_RAW_BONFERRONI")]["covered"]
                r4 = by[(wid, "R4_PERSISTENT_RIEC_BROKER")]["covered"]
                h2_fav += int(r4 and not b1)
                h2_adv += int(b1 and not r4)
        h1p = protocol.exact_sign_p(h1_fav, h1_adv)
        h2p = protocol.exact_sign_p(h2_fav, h2_adv)
        holm = protocol.holm([
            ("H1_R4_LT_B3_NULL_RISK", h1p),
            ("H2_R4_GT_B1_ALIAS_COVERAGE", h2p),
        ])
        return {
            "label": label,
            "worlds": len(selected_worlds),
            "H1": {"favorable": h1_fav, "adverse": h1_adv, "p_value_one_sided": h1p},
            "H2": {"favorable": h2_fav, "adverse": h2_adv, "p_value_one_sided": h2p},
            "holm": holm,
            "holm_all_pass": all(row["reject"] for row in holm),
            "B3_MULTI_NULL_RISK": rate(selected_worlds, "B3_LOCAL_IDENTITY_BONFERRONI", "NULL", "unsupported", True),
            "R4_MULTI_NULL_RISK": rate(selected_worlds, "R4_PERSISTENT_RIEC_BROKER", "NULL", "unsupported", True),
            "B1_ALIAS_SIGNAL_COVERAGE": rate(selected_worlds, "B1_GLOBAL_RAW_BONFERRONI", "SIGNAL", "covered", True),
            "R4_ALIAS_SIGNAL_COVERAGE": rate(selected_worlds, "R4_PERSISTENT_RIEC_BROKER", "SIGNAL", "covered", True),
            "B3_SIGNAL_COVERAGE_DESCRIPTIVE": rate(selected_worlds, "B3_LOCAL_IDENTITY_BONFERRONI", "SIGNAL", "covered", True),
            "R4_SIGNAL_FALSE_BLOCK": rate(selected_worlds, "R4_PERSISTENT_RIEC_BROKER", "SIGNAL", "false_block", True),
            "R4_ALL_NULL_RISK_DESCRIPTIVE": rate(selected_worlds, "R4_PERSISTENT_RIEC_BROKER", "NULL", "unsupported", False),
        }

    available = evaluate(worlds, "ALL_120_WORLDS_WITH_8_TRANSPORT_EVENTS_ABSENT")
    complete_worlds = [world for world in worlds if world["world_id"] not in affected_worlds]
    complete_case = evaluate(complete_worlds, "114_WORLDS_WITH_NO_TRANSPORT_MISSINGNESS")

    h1_worst_fav = complete_case["H1"]["favorable"]
    h1_worst_adv = complete_case["H1"]["adverse"] + len(affected_worlds)
    h1_worst_p = protocol.exact_sign_p(h1_worst_fav, h1_worst_adv)
    h2_p = complete_case["H2"]["p_value_one_sided"]
    worst_holm = protocol.holm([
        ("H1_R4_LT_B3_NULL_RISK", h1_worst_p),
        ("H2_R4_GT_B1_ALIAS_COVERAGE", h2_p),
    ])
    extreme = {
        "description": "All six transport-affected worlds are assigned as H1 discordances adverse to R4; H2 is unchanged because every affected world is NULL.",
        "H1": {"favorable": h1_worst_fav, "adverse": h1_worst_adv, "p_value_one_sided": h1_worst_p},
        "H2_p_value_one_sided": h2_p,
        "holm": worst_holm,
        "holm_all_pass": all(row["reject"] for row in worst_holm),
    }

    regime_rows = []
    for regime in sorted({world["risk_regime"] for world in worlds}):
        selected = [world for world in worlds if world["risk_regime"] == regime]
        truth = selected[0]["truth_class_public"]
        arms = protocol.NULL_ARMS if truth == "NULL" else protocol.SIGNAL_ARMS
        endpoint = "unsupported" if truth == "NULL" else "covered"
        for arm in arms:
            metric = rate(selected, arm, truth, endpoint, False)
            regime_rows.append({"risk_regime": regime, "truth_class": truth, "arm": arm, "endpoint": endpoint, **metric})
    write_json(ANALYSIS / "RISK_REGIME_SUMMARY.json", regime_rows)

    result = {
        "adjudication_status": "COMPLETED",
        "original_confirmatory_status_preserved": "FAIL_CLOSED_BEFORE_C",
        "analysis_authority": "POST_FAILURE_USER_AUTHORIZED_AVAILABLE_CASE",
        "model_id": protocol.MODEL_ID,
        "planned_sessions": len(schedule),
        "accepted_sessions": len(accepted),
        "transport_missing_sessions": len(missing),
        "transport_completion_rate": len(accepted) / len(schedule),
        "affected_worlds": affected_worlds,
        "all_missing_zero_token_zero_response": all_transport_only,
        "R4_ALPHA_INVARIANT": alpha_ok,
        "available_case": available,
        "complete_world_sensitivity": complete_case,
        "extreme_missingness_sensitivity": extreme,
        "claim_boundary": "Qwen-specific synthetic evidence-market behavior. This post-failure available-case analysis is not a pristine prospective confirmation, not universal AI-agent validity, and not real-world scientific benefit.",
    }
    write_json(ANALYSIS / "QWEN_AVAILABLE_CASE_ANALYSIS.json", result)

    def pct(metric):
        return f"{100 * metric['rate']:.1f}% ({metric['numerator']}/{metric['denominator']})"

    conclusion = "PASS" if available["holm_all_pass"] else "FAIL"
    robustness = "PASS" if complete_case["holm_all_pass"] else "FAIL"
    extreme_status = "PASS" if extreme["holm_all_pass"] else "FAIL"
    report = f"""# Qwen v1.6.1 available-case result

## Bottom line

The 1,912 returned sessions produce an available-case joint result of **{conclusion}**. The complete-world sensitivity result, which removes all six worlds touched by a transport failure, is **{robustness}**. Under the deliberately extreme assumption that every affected world would have favored B3 over R4, the joint result is **{extreme_status}**.

This does not rewrite the original run: its preregistered all-complete confirmation status remains `FAIL_CLOSED_BEFORE_C`. The result below has `POST_FAILURE_USER_AUTHORIZED_AVAILABLE_CASE` authority.

## Main numerical result

- B3 multi-claim null risk: **{pct(available['B3_MULTI_NULL_RISK'])}**
- R4 persistent-broker multi-claim null risk: **{pct(available['R4_MULTI_NULL_RISK'])}**
- B1 alias-signal coverage: **{pct(available['B1_ALIAS_SIGNAL_COVERAGE'])}**
- R4 persistent-broker alias-signal coverage: **{pct(available['R4_ALIAS_SIGNAL_COVERAGE'])}**
- H1 paired evidence: favorable `{available['H1']['favorable']}`, adverse `{available['H1']['adverse']}`, one-sided p=`{available['H1']['p_value_one_sided']:.8g}`
- H2 paired evidence: favorable `{available['H2']['favorable']}`, adverse `{available['H2']['adverse']}`, one-sided p=`{available['H2']['p_value_one_sided']:.8g}`
- Holm family pass: **{str(available['holm_all_pass']).upper()}**
- R4 alpha-ledger invariant: **{str(alpha_ok).upper()}**

## Missingness sensitivity

- Planned sessions: `{len(schedule)}`
- Accepted sessions: `{len(accepted)}`
- Zero-token transport-missing sessions: `{len(missing)}`
- Completion rate: `{100 * len(accepted) / len(schedule):.3f}%`
- Worlds touched by transport failure: `{len(affected_worlds)}`; all were NULL worlds, so H2 signal coverage is unaffected.
- Complete-world H1: favorable `{complete_case['H1']['favorable']}`, adverse `{complete_case['H1']['adverse']}`, p=`{complete_case['H1']['p_value_one_sided']:.8g}`
- Complete-world H2: favorable `{complete_case['H2']['favorable']}`, adverse `{complete_case['H2']['adverse']}`, p=`{complete_case['H2']['p_value_one_sided']:.8g}`
- Extreme adverse H1 bound: favorable `{extreme['H1']['favorable']}`, adverse `{extreme['H1']['adverse']}`, p=`{extreme['H1']['p_value_one_sided']:.8g}`; Holm family pass **{str(extreme['holm_all_pass']).upper()}**

## Interpretation boundary

These results test whether a persistent evidence broker controls unsupported claims while preserving discovery in this frozen synthetic multi-agent evidence market. They do not prove universal superiority over every correction method, universal Qwen behavior, or real-world scientific benefit.
"""
    (OUT / "01_PLAIN_LANGUAGE_RESULT.md").write_text(report, encoding="utf-8")

    manifest_rows = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name not in {"FINAL_MANIFEST.csv", "FINAL_CHECKSUMS_SHA256.txt"}:
            manifest_rows.append({
                "path": str(path.relative_to(OUT)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    with (OUT / "FINAL_MANIFEST.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)
    checksum_rows = manifest_rows + [{
        "path": "FINAL_MANIFEST.csv",
        "bytes": (OUT / "FINAL_MANIFEST.csv").stat().st_size,
        "sha256": sha256(OUT / "FINAL_MANIFEST.csv"),
    }]
    (OUT / "FINAL_CHECKSUMS_SHA256.txt").write_text(
        "".join(f"{row['sha256']}  {row['path']}\n" for row in checksum_rows),
        encoding="utf-8",
    )

    print(f"AVAILABLE_CASE_STATUS={conclusion}")
    print(f"COMPLETE_WORLD_SENSITIVITY={robustness}")
    print(f"EXTREME_MISSINGNESS_SENSITIVITY={extreme_status}")
    print(f"ACCEPTED_SESSIONS={len(accepted)}/{len(schedule)}")
    print(f"OUTPUT_DIR={OUT}")


if __name__ == "__main__":
    main()
