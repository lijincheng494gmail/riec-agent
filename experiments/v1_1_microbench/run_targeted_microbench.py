#!/usr/bin/env python3
"""Execute frozen targeted cases and mutation testing."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from microbench_engine import evaluate_case, matches_expected  # noqa: E402


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    protocol = json.loads((ROOT / "01_MICROBENCH_PROTOCOL.json").read_text())
    cases = json.loads((ROOT / "02_TARGETED_CASES.json").read_text())
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)

    case_rows = []
    evaluations = {}
    for case in cases:
        evaluation = evaluate_case(case)
        evaluations[case["case_id"]] = evaluation
        matched = matches_expected(evaluation, case["expected"])
        case_rows.append({
            "case_id": case["case_id"],
            "risk_regime": case["risk_regime"],
            "kind": case["kind"],
            "authority": evaluation.authority,
            "expected_authority": case["expected"]["authority"],
            "action": evaluation.action,
            "expected_action": case["expected"]["action"],
            "core_failures": "|".join(evaluation.core_failures),
            "expected_core_failures": "|".join(case["expected"]["core_failures"]),
            "triggered_rules": "|".join(evaluation.triggered_rules),
            "expected_triggered_rules": "|".join(case["expected"]["triggered_rules"]),
            "expectation_match": int(matched),
        })
    write_csv(results_dir / "06_CASE_RESULTS.csv", case_rows)

    coverage_rows = []
    risk_regimes = sorted({case["risk_regime"] for case in cases})
    core_gates = sorted({gate for evaluation in evaluations.values() for gate in evaluation.core_failures})
    agent_rules = sorted({rule for evaluation in evaluations.values() for rule in evaluation.triggered_rules})
    for item_type, required, observed in (
        ("RISK_REGIME", protocol["required_risk_regimes"], risk_regimes),
        ("CORE_GATE", protocol["required_core_gate_coverage"], core_gates),
        ("AGENT_RULE", protocol["required_agent_rule_coverage"], agent_rules),
    ):
        for item in required:
            activating_cases = [
                case["case_id"] for case in cases
                if (item_type == "RISK_REGIME" and case["risk_regime"] == item)
                or (item_type == "CORE_GATE" and item in evaluations[case["case_id"]].core_failures)
                or (item_type == "AGENT_RULE" and item in evaluations[case["case_id"]].triggered_rules)
            ]
            coverage_rows.append({
                "item_type": item_type,
                "item_id": item,
                "covered": int(item in observed),
                "activating_cases": "|".join(activating_cases),
            })
    write_csv(results_dir / "07_ACTIVATION_COVERAGE.csv", coverage_rows)

    mutation_rows = []
    for mutant in protocol["mutants"]:
        killed_by = []
        for case in cases:
            mutant_evaluation = evaluate_case(case, mutant=mutant)
            if not matches_expected(mutant_evaluation, case["expected"]):
                killed_by.append(case["case_id"])
        mutation_rows.append({
            "mutant": mutant,
            "killed": int(bool(killed_by)),
            "first_killing_case": killed_by[0] if killed_by else "",
            "killing_case_count": len(killed_by),
        })
    write_csv(results_dir / "08_MUTATION_RESULTS.csv", mutation_rows)

    matched_count = sum(row["expectation_match"] for row in case_rows)
    control_false_activation = sum(
        bool(row["core_failures"] or row["triggered_rules"])
        for row in case_rows if row["kind"] == "CONTROL"
    )
    covered_count = sum(row["covered"] for row in coverage_rows)
    mutation_killed = sum(row["killed"] for row in mutation_rows)
    all_pass = all((
        matched_count == len(case_rows),
        control_false_activation == 0,
        covered_count == len(coverage_rows),
        mutation_killed == len(mutation_rows),
    ))
    report = f"""# Targeted risk-activation microbenchmark report

Status: `{'PASS' if all_pass else 'FAIL'}`

## Exact case behavior

- Cases matching prospectively declared authority/gate/rule/action expectations: `{matched_count}/{len(case_rows)}`
- False gate/rule activations in matched controls: `{control_false_activation}`
- Required activation items covered: `{covered_count}/{len(coverage_rows)}`
- Risk regimes covered: `{len(risk_regimes)}/8`
- Core gates activated by targeted risks: `{len(core_gates)}/7`
- Required Agent rules activated: `{len(protocol['required_agent_rule_coverage'])}/{len(protocol['required_agent_rule_coverage'])}`

## Mutation sensitivity

- Deliberately defective adjudicators killed: `{mutation_killed}/{len(mutation_rows)}`
- Mutation score: `{mutation_killed / len(mutation_rows):.1%}`

The mutation suite includes ignored G0-G6 gates, per-agent budget reset, agent-consensus pseudo-replication, invalid sequential testing, unadjusted final multiplicity, repeated/contaminated confirmation access, confirmation-based route selection, ignored practical thresholds or missingness, development-effect promotion, version mutation and an incorrect penalty on extensive development search.

## Boundary

Passing means that the deterministic cases activate the intended mechanisms and detect the declared defective implementations. It does not establish real-agent behavior, calibrated empirical effect size or publication-level component necessity.
"""
    (results_dir / "09_MICROBENCH_REPORT.md").write_text(report, encoding="utf-8")
    print(f"TARGETED_MICROBENCH={'PASS' if all_pass else 'FAIL'}")
    print(f"CASE_EXPECTATIONS={matched_count}/{len(case_rows)}")
    print(f"MUTANTS_KILLED={mutation_killed}/{len(mutation_rows)}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())

