#!/usr/bin/env python3
"""Run the frozen synthetic outcome-blind rule-behavior simulation."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import NormalDist, mean


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
CONFIG_PATH = ROOT / "01_SIMULATION_PROTOCOL.json"
CURVES = RESULTS / "06_SIMULATION_CURVES.csv"
SUMMARY = RESULTS / "07_SIMULATION_SUMMARY.csv"
REPORT = RESULTS / "08_OUTCOME_BLIND_SIMULATION_REPORT.md"
NORMAL = NormalDist()


def scenario_rng(master_seed: int, label: str) -> random.Random:
    material = f"{master_seed}:{label}".encode("utf-8")
    seed = int(hashlib.sha256(material).hexdigest()[:16], 16)
    return random.Random(seed)


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n < 1:
        return (math.nan, math.nan)
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return center - half, center + half


def row(
    scenario: str,
    policy: str,
    level: int,
    n: int,
    false_claims: int,
    true_claims: int | None = None,
    true_opportunities: int | None = None,
    development_winners: int | None = None,
    selection_optimism: float | None = None,
) -> dict[str, object]:
    low, high = wilson(false_claims, n)
    coverage = ""
    if true_claims is not None and true_opportunities:
        coverage = true_claims / true_opportunities
    return {
        "scenario": scenario,
        "policy": policy,
        "level": level,
        "replicates": n,
        "false_claims": false_claims,
        "false_claim_rate": false_claims / n,
        "false_claim_wilson95_low": low,
        "false_claim_wilson95_high": high,
        "true_claims": "" if true_claims is None else true_claims,
        "true_opportunities": "" if true_opportunities is None else true_opportunities,
        "true_claim_coverage": coverage,
        "development_winner_rate": "" if development_winners is None else development_winners / n,
        "mean_selection_optimism": "" if selection_optimism is None else selection_optimism,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def simulate_one_shot(config: dict, rows: list[dict[str, object]]) -> None:
    n = config["replicates"]
    alpha = config["alpha"]
    signal_mu = config["signal_z_mean"]
    zcrit = NORMAL.inv_cdf(1 - alpha)
    for budget in config["development_search_budgets"]:
        rng = scenario_rng(config["master_seed"], f"one-shot-{budget}")
        null_reject = 0
        alt_reject = 0
        dev_winner = 0
        optimism = []
        for _ in range(n):
            u = min(max(rng.random(), 1e-15), 1 - 1e-15)
            max_cdf = u ** (1 / budget)
            dev_max = NORMAL.inv_cdf(min(max(max_cdf, 1e-15), 1 - 1e-15))
            c_null = rng.gauss(0, 1)
            c_alt = rng.gauss(signal_mu, 1)
            null_reject += c_null >= zcrit
            alt_reject += c_alt >= zcrit
            dev_winner += dev_max >= zcrit
            optimism.append(dev_max - c_null)
        for policy in ("B2_PROTECTED_ONE_SHOT", "B5_V11_HYBRID_R0"):
            rows.append(row(
                "R0_ONE_SHOT",
                policy,
                budget,
                n,
                null_reject,
                alt_reject,
                n,
                dev_winner,
                mean(optimism),
            ))


def simulate_minimum_p_family(
    config: dict,
    rows: list[dict[str, object]],
    scenario: str,
    levels: list[int],
    naive_policy: str,
    controlled_policy: str,
) -> None:
    n = config["replicates"]
    alpha = config["alpha"]
    for level in levels:
        rng = scenario_rng(config["master_seed"], f"{scenario}-{level}")
        naive = 0
        controlled = 0
        for _ in range(n):
            u = rng.random()
            min_p = 1 - (1 - u) ** (1 / level)
            naive += min_p <= alpha
            controlled += min_p <= alpha / level
        rows.append(row(scenario, naive_policy, level, n, naive))
        rows.append(row(scenario, controlled_policy, level, n, controlled))


def simulate_structural_mismatch(config: dict, rows: list[dict[str, object]]) -> None:
    n = config["replicates"]
    alpha = config["alpha"]
    invalid_probability = config["structural_invalid_probability"]
    zcrit = NORMAL.inv_cdf(1 - alpha)
    rng = scenario_rng(config["master_seed"], "structural-mismatch")
    numerical_unsupported = 0
    hybrid_unsupported = 0
    numerical_true = 0
    hybrid_true = 0
    valid_opportunities = 0
    for _ in range(n):
        structurally_valid = rng.random() >= invalid_probability
        significant = rng.gauss(config["signal_z_mean"], 1) >= zcrit
        if structurally_valid:
            valid_opportunities += 1
            numerical_true += significant
            hybrid_true += significant
        else:
            numerical_unsupported += significant
            hybrid_unsupported += 0
    rows.append(row(
        "R5_STRUCTURAL_MISMATCH",
        "B4_NUMERICAL_ONLY",
        1,
        n,
        numerical_unsupported,
        numerical_true,
        valid_opportunities,
    ))
    rows.append(row(
        "R5_STRUCTURAL_MISMATCH",
        "B5_V11_HYBRID",
        1,
        n,
        hybrid_unsupported,
        hybrid_true,
        valid_opportunities,
    ))


def evaluate_acceptance(config: dict, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rules = config["acceptance_rules"]
    keyed = {(r["scenario"], r["policy"], r["level"]): r for r in rows}
    checks: list[dict[str, object]] = []

    one_shot = [
        keyed[("R0_ONE_SHOT", "B2_PROTECTED_ONE_SHOT", budget)]["false_claim_rate"]
        for budget in config["development_search_budgets"]
    ]
    checks.append({
        "check_id": "AC-001",
        "description": "One-shot false-claim rate remains controlled across development budgets",
        "observed": max(one_shot),
        "criterion": f"max <= {rules['maximum_controlled_global_null_rate']}",
        "status": "PASS" if max(one_shot) <= rules["maximum_controlled_global_null_rate"] else "FAIL",
    })
    checks.append({
        "check_id": "AC-002",
        "description": "One-shot rate does not drift with development search budget",
        "observed": max(one_shot) - min(one_shot),
        "criterion": f"range <= {rules['maximum_one_shot_rate_range_across_search_budgets']}",
        "status": "PASS" if max(one_shot) - min(one_shot) <= rules["maximum_one_shot_rate_range_across_search_budgets"] else "FAIL",
    })
    equality = all(
        keyed[("R0_ONE_SHOT", "B2_PROTECTED_ONE_SHOT", budget)]["false_claims"]
        == keyed[("R0_ONE_SHOT", "B5_V11_HYBRID_R0", budget)]["false_claims"]
        and keyed[("R0_ONE_SHOT", "B2_PROTECTED_ONE_SHOT", budget)]["true_claims"]
        == keyed[("R0_ONE_SHOT", "B5_V11_HYBRID_R0", budget)]["true_claims"]
        for budget in config["development_search_budgets"]
    )
    checks.append({
        "check_id": "AC-003",
        "description": "Hybrid exactly preserves the competent one-shot baseline in R0",
        "observed": int(equality),
        "criterion": "equal false claims and true claims at every budget",
        "status": "PASS" if equality else "FAIL",
    })

    naive_q1 = keyed[("R1_REUSABLE_HOLDOUT", "B1_NAIVE_REUSE", 1)]["false_claim_rate"]
    naive_q100 = keyed[("R1_REUSABLE_HOLDOUT", "B1_NAIVE_REUSE", 100)]["false_claim_rate"]
    inflation = naive_q100 - naive_q1
    checks.append({
        "check_id": "AC-004",
        "description": "Naive repeated holdout access exhibits large false-claim inflation",
        "observed": inflation,
        "criterion": f"q100-q1 >= {rules['minimum_naive_reuse_inflation_q100_minus_q1']}",
        "status": "PASS" if inflation >= rules["minimum_naive_reuse_inflation_q100_minus_q1"] else "FAIL",
    })

    controlled_policies = {
        "B5_GLOBAL_QUERY_CONTROL",
        "B5_GLOBAL_MULTIAGENT_CONTROL",
        "B5_FINAL_HOLM_CONTROL",
    }
    controlled_rates = [r["false_claim_rate"] for r in rows if r["policy"] in controlled_policies]
    checks.append({
        "check_id": "AC-005",
        "description": "Global repeated-access and final-family controllers preserve null error",
        "observed": max(controlled_rates),
        "criterion": f"max <= {rules['maximum_controlled_global_null_rate']}",
        "status": "PASS" if max(controlled_rates) <= rules["maximum_controlled_global_null_rate"] else "FAIL",
    })

    numerical = keyed[("R5_STRUCTURAL_MISMATCH", "B4_NUMERICAL_ONLY", 1)]
    hybrid = keyed[("R5_STRUCTURAL_MISMATCH", "B5_V11_HYBRID", 1)]
    checks.append({
        "check_id": "AC-006",
        "description": "Numerical-only validation admits structurally unsupported claims",
        "observed": numerical["false_claim_rate"],
        "criterion": f">= {rules['minimum_structural_unsupported_rate_for_numerical_only']}",
        "status": "PASS" if numerical["false_claim_rate"] >= rules["minimum_structural_unsupported_rate_for_numerical_only"] else "FAIL",
    })
    checks.append({
        "check_id": "AC-007",
        "description": "Hybrid blocks structurally invalid claims",
        "observed": hybrid["false_claim_rate"],
        "criterion": f"== {rules['maximum_structural_unsupported_rate_for_hybrid']}",
        "status": "PASS" if hybrid["false_claim_rate"] == rules["maximum_structural_unsupported_rate_for_hybrid"] else "FAIL",
    })
    power_difference = abs(float(numerical["true_claim_coverage"]) - float(hybrid["true_claim_coverage"]))
    checks.append({
        "check_id": "AC-008",
        "description": "Structural gate does not reduce coverage for structurally valid claims in this oracle test",
        "observed": power_difference,
        "criterion": f"<= {rules['valid_structural_power_difference_tolerance']}",
        "status": "PASS" if power_difference <= rules["valid_structural_power_difference_tolerance"] else "FAIL",
    })
    return checks


def build_report(config: dict, rows: list[dict[str, object]], checks: list[dict[str, object]]) -> str:
    keyed = {(r["scenario"], r["policy"], r["level"]): r for r in rows}
    all_pass = all(check["status"] == "PASS" for check in checks)
    one_shot = [keyed[("R0_ONE_SHOT", "B2_PROTECTED_ONE_SHOT", b)] for b in config["development_search_budgets"]]
    naive = [keyed[("R1_REUSABLE_HOLDOUT", "B1_NAIVE_REUSE", q)] for q in config["reusable_holdout_queries"]]
    controlled = [keyed[("R1_REUSABLE_HOLDOUT", "B5_GLOBAL_QUERY_CONTROL", q)] for q in config["reusable_holdout_queries"]]
    numerical = keyed[("R5_STRUCTURAL_MISMATCH", "B4_NUMERICAL_ONLY", 1)]
    hybrid = keyed[("R5_STRUCTURAL_MISMATCH", "B5_V11_HYBRID", 1)]
    return f"""# Outcome-blind simulation report

Status: `{'PASS' if all_pass else 'FAIL'}`

This deterministic Monte Carlo run used only synthetic random variables generated from the frozen protocol. It did not use prior provider outcomes, private campaign truth or Neuro artifacts.

## One-shot sufficiency

Across development search budgets {config['development_search_budgets']}, one untouched final test had false-claim rates {[round(r['false_claim_rate'], 4) for r in one_shot]}. The hybrid and protected one-shot baseline used the same frozen decision and were exactly equal at every budget. Development winner rates increased to {[round(r['development_winner_rate'], 4) for r in one_shot]}, demonstrating selection pressure without inflating the independent final test.

## Reusable holdout

For query counts {config['reusable_holdout_queries']}, naive repeated testing produced false-claim rates {[round(r['false_claim_rate'], 4) for r in naive]}. Global query accounting produced {[round(r['false_claim_rate'], 4) for r in controlled]}.

## Structural mismatch

When {config['structural_invalid_probability']:.0%} of otherwise numerically favorable opportunities were structurally inadmissible, numerical-only validation produced an unsupported-confirmation rate of {numerical['false_claim_rate']:.4f}; the hybrid produced {hybrid['false_claim_rate']:.4f}. Coverage among structurally valid opportunities was identical at {float(hybrid['true_claim_coverage']):.4f}.

## Frozen acceptance checks

""" + "\n".join(
        f"- `{check['check_id']}` `{check['status']}` — {check['description']}: observed={check['observed']}; {check['criterion']}"
        for check in checks
    ) + f"""

## Interpretation boundary

`SIMULATION_VALIDATION={'PASS' if all_pass else 'FAIL'}` means only that the reference rules behaved as specified under the frozen synthetic generators. It does not establish empirical effectiveness, provider robustness, real scientific validity or publication-level RIEC-Agent superiority.
"""


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    RESULTS.mkdir(exist_ok=True)
    rows: list[dict[str, object]] = []
    simulate_one_shot(config, rows)
    simulate_minimum_p_family(
        config,
        rows,
        "R1_REUSABLE_HOLDOUT",
        config["reusable_holdout_queries"],
        "B1_NAIVE_REUSE",
        "B5_GLOBAL_QUERY_CONTROL",
    )
    totals = [count * config["queries_per_agent"] for count in config["multiagent_counts"]]
    simulate_minimum_p_family(
        config,
        rows,
        "R2_MULTIAGENT_SHARED_Q",
        totals,
        "B1_PER_AGENT_RESET",
        "B5_GLOBAL_MULTIAGENT_CONTROL",
    )
    simulate_minimum_p_family(
        config,
        rows,
        "R3_MULTICLAIM_FINAL",
        config["final_claim_counts"],
        "B1_UNADJUSTED_FINAL_CLAIMS",
        "B5_FINAL_HOLM_CONTROL",
    )
    simulate_structural_mismatch(config, rows)
    write_csv(CURVES, rows)
    checks = evaluate_acceptance(config, rows)
    write_csv(SUMMARY, checks)
    REPORT.write_text(build_report(config, rows, checks), encoding="utf-8")
    passed = all(check["status"] == "PASS" for check in checks)
    print(f"SIMULATION_VALIDATION={'PASS' if passed else 'FAIL'}")
    print(f"SIMULATION_ROWS={len(rows)}")
    print(f"ACCEPTANCE_CHECKS={len(checks)}")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

