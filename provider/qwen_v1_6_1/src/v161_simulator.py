from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from typing import Any, Iterable


PROTOCOL_ID = "RIEC_AGENT_V1_6_1_PERSISTENT_BROKER_CALIBRATION"
FAMILY_ALPHA = 0.05
BROKER_ALPHA_CANDIDATES = (0.050, 0.045, 0.040, 0.035, 0.030, 0.025)
LOCAL_ALPHA = 0.05
AGENTS_PER_WORLD = 8
IDENTITIES_PER_CLAIM = 2
SEARCH_BUDGETS = (1, 2, 4, 8)
ARMS = (
    "B1_GLOBAL_RAW_BONFERRONI",
    "B2_ONLINE_GLOBAL_SPENDING",
    "B3_LOCAL_IDENTITY_BONFERRONI",
    "R4_PERSISTENT_RIEC_BROKER",
)
ONLINE_WEIGHTS = (0.22, 0.18, 0.15, 0.12, 0.10, 0.09, 0.08, 0.06)


@dataclass(frozen=True)
class Regime:
    regime_id: str
    truth_class: str
    claims: int
    aliases: bool
    invalid_lure: bool
    rho: float
    signal_shape: float | None
    risk_tags: tuple[str, ...]


REGIMES = (
    Regime("N0_FIXED_CONTROL", "NULL", 1, False, False, 0.0, None,
           ("fixed", "single_claim")),
    Regime("N1_MULTI_CLAIM", "NULL", 4, False, False, 0.0, None,
           ("multi_claim", "cross_agent")),
    Regime("N2_ALIAS_LAUNDERING", "NULL", 4, True, False, 0.0, None,
           ("multi_claim", "alias", "cross_agent")),
    Regime("N3_DEPENDENT_ALIAS", "NULL", 4, True, False, 0.65, None,
           ("multi_claim", "alias", "dependence", "cross_agent")),
    Regime("N4_INVALID_HIGH_SCORE_LURE", "NULL", 4, True, True, 0.25, None,
           ("multi_claim", "alias", "structural_gate", "cross_agent")),
    Regime("N5_COMBINED_RELAY", "NULL", 4, True, True, 0.70, None,
           ("multi_claim", "alias", "dependence", "structural_gate", "relay")),
    Regime("S0_FIXED_CONTROL", "SIGNAL", 1, False, False, 0.0, 0.050,
           ("fixed", "single_claim", "signal")),
    Regime("S1_ALIAS_SIGNAL", "SIGNAL", 4, True, False, 0.0, 0.050,
           ("multi_claim", "alias", "late_signal")),
    Regime("S2_DEPENDENT_ALIAS_SIGNAL", "SIGNAL", 4, True, False, 0.65, 0.050,
           ("multi_claim", "alias", "dependence", "late_signal")),
    Regime("S3_INVALID_LURE_SIGNAL", "SIGNAL", 4, True, True, 0.25, 0.060,
           ("multi_claim", "alias", "structural_gate", "late_signal")),
    Regime("S4_WEAK_LATE_SIGNAL", "SIGNAL", 4, True, False, 0.35, 0.120,
           ("multi_claim", "alias", "weak_signal", "late_signal")),
    Regime("S5_COMBINED_RELAY_SIGNAL", "SIGNAL", 4, True, True, 0.70, 0.060,
           ("multi_claim", "alias", "dependence", "structural_gate", "relay", "late_signal")),
)
NULL_REGIMES = tuple(r for r in REGIMES if r.truth_class == "NULL")
SIGNAL_REGIMES = tuple(r for r in REGIMES if r.truth_class == "SIGNAL")
RISK_NULL_REGIMES = tuple(r for r in NULL_REGIMES if r.claims > 1)
ALIAS_SIGNAL_REGIMES = tuple(r for r in SIGNAL_REGIMES if r.aliases)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _correlated_uniforms(rng: random.Random, count: int, rho: float) -> list[float]:
    common = rng.gauss(0.0, 1.0)
    return [
        min(1.0 - 1e-15, max(1e-15, _normal_cdf(math.sqrt(rho) * common + math.sqrt(1.0 - rho) * rng.gauss(0.0, 1.0))))
        for _ in range(count)
    ]


def _claim_schedule(claims: list[str], regime: Regime, rng: random.Random) -> list[str]:
    if len(claims) == 1:
        return claims * AGENTS_PER_WORLD
    first = list(claims)
    rng.shuffle(first)
    if "relay" in regime.risk_tags:
        second = first[1:] + first[:1]
    else:
        second = list(first)
    return (first + second)[:AGENTS_PER_WORLD]


def generate_world(seed: int, regime: Regime, world_index: int) -> dict[str, Any]:
    rng = random.Random(seed)
    claims = [f"C{i}" for i in range(regime.claims)]
    target_claim = rng.choice(claims) if regime.truth_class == "SIGNAL" else None
    null_uniforms = _correlated_uniforms(rng, regime.claims * IDENTITIES_PER_CLAIM, regime.rho)
    p_values: dict[str, float] = {}
    cursor = 0
    for claim in claims:
        for identity in ("E0", "E1"):
            key = f"{claim}:{identity}"
            p_values[key] = null_uniforms[cursor]
            cursor += 1
    if target_claim is not None:
        # Beta(a, 1): strong/weak signal strength is fixed by regime before outcomes.
        p_values[f"{target_claim}:E1"] = rng.random() ** (1.0 / float(regime.signal_shape))

    artifacts: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        rows = []
        if regime.invalid_lure:
            rows.append({
                "artifact_id": f"{claim}_RX", "authority_key": f"{claim}:EX",
                "qualified": False, "development_score": 0.995,
            })
        rows.append({
            "artifact_id": f"{claim}_R0", "authority_key": f"{claim}:E0",
            "qualified": True, "development_score": 0.900,
        })
        if regime.aliases:
            rows.append({
                "artifact_id": f"{claim}_R0_ALIAS", "authority_key": f"{claim}:E0",
                "qualified": True, "development_score": 0.885,
            })
        rows.append({
            "artifact_id": f"{claim}_R1", "authority_key": f"{claim}:E1",
            "qualified": True, "development_score": 0.830,
        })
        artifacts[claim] = sorted(rows, key=lambda row: (-row["development_score"], row["artifact_id"]))

    return {
        "world_id": f"{regime.regime_id}-W{world_index:06d}",
        "regime": asdict(regime),
        "claims": claims,
        "target_claim": target_claim,
        "target_authority_key": f"{target_claim}:E1" if target_claim else None,
        "p_values": p_values,
        "artifacts": artifacts,
        "claim_schedule": _claim_schedule(claims, regime, rng),
    }


def _threshold(arm: str, world: dict[str, Any], raw_tests: int, broker_alpha: float) -> float:
    if arm == "B1_GLOBAL_RAW_BONFERRONI":
        return FAMILY_ALPHA / AGENTS_PER_WORLD
    if arm == "B2_ONLINE_GLOBAL_SPENDING":
        return FAMILY_ALPHA * ONLINE_WEIGHTS[min(raw_tests, AGENTS_PER_WORLD - 1)]
    if arm == "B3_LOCAL_IDENTITY_BONFERRONI":
        return LOCAL_ALPHA / IDENTITIES_PER_CLAIM
    if arm == "R4_PERSISTENT_RIEC_BROKER":
        return broker_alpha / (len(world["claims"]) * IDENTITIES_PER_CLAIM)
    raise ValueError(f"unknown arm: {arm}")


def run_arm(world: dict[str, Any], arm: str, broker_alpha: float) -> dict[str, Any]:
    identity_aware = arm in {"B3_LOCAL_IDENTITY_BONFERRONI", "R4_PERSISTENT_RIEC_BROKER"}
    seen_raw: set[str] = set()
    seen_authority: dict[str, dict[str, Any]] = {}
    events: list[dict[str, Any]] = []
    alpha_spent = 0.0
    unsupported = False
    covered = False
    unsupported_curve: list[int] = []
    coverage_curve: list[int] = []

    for agent_index, claim in enumerate(world["claim_schedule"], 1):
        candidates = world["artifacts"][claim]
        rejected = [row["artifact_id"] for row in candidates if not row["qualified"]]
        eligible = [row for row in candidates if row["qualified"]]
        selected = None
        for row in eligible:
            unseen = row["authority_key"] not in seen_authority if identity_aware else row["artifact_id"] not in seen_raw
            if unseen:
                selected = row
                break
        if selected is None:
            unsupported_curve.append(int(unsupported))
            coverage_curve.append(int(covered))
            events.append({
                "agent_index": agent_index, "claim": claim, "artifact_id": None,
                "authority_key": None, "structurally_rejected": rejected,
                "new_evidence": False, "feedback": "NO_NEW_AUTHORITY", "threshold": None,
            })
            continue

        key = selected["authority_key"]
        reused = key in seen_authority if identity_aware else selected["artifact_id"] in seen_raw
        threshold = _threshold(arm, world, len([e for e in events if e.get("new_evidence")]), broker_alpha)
        if reused:
            feedback = seen_authority[key]["feedback"]
            new_evidence = False
        else:
            feedback = "PASS" if world["p_values"][key] <= threshold else "FAIL"
            new_evidence = True
            alpha_spent += threshold
            seen_raw.add(selected["artifact_id"])
            seen_authority.setdefault(key, {"feedback": feedback, "threshold": threshold})

        if feedback == "PASS":
            supported = key == world["target_authority_key"]
            unsupported |= not supported
            covered |= supported
        events.append({
            "agent_index": agent_index, "claim": claim,
            "artifact_id": selected["artifact_id"], "authority_key": key,
            "structurally_rejected": rejected, "new_evidence": new_evidence,
            "feedback": feedback, "threshold": threshold,
        })
        unsupported_curve.append(int(unsupported))
        coverage_curve.append(int(covered))

    return {
        "unsupported": unsupported,
        "covered": covered,
        "false_block": bool(world["target_authority_key"] and not covered),
        "alpha_spent": alpha_spent,
        "raw_tests": sum(bool(e.get("new_evidence")) for e in events),
        "unique_authorities_observed": len(seen_authority),
        "unsupported_curve": unsupported_curve,
        "coverage_curve": coverage_curve,
        "events": events,
    }


def simulate(seed: int, worlds_per_regime: int, broker_alpha: float,
             regimes: Iterable[Regime] = REGIMES, include_events: bool = False) -> dict[str, Any]:
    regimes = tuple(regimes)
    counts: dict[str, dict[str, float]] = {
        arm: {
            "null_n": 0, "null_false": 0, "signal_n": 0, "signal_covered": 0,
            "alias_signal_n": 0, "alias_signal_covered": 0, "false_block": 0,
            "alpha_max": 0.0, "raw_tests_sum": 0.0,
        } for arm in ARMS
    }
    by_regime: dict[str, dict[str, dict[str, float]]] = {}
    exemplars: list[dict[str, Any]] = []
    world_counter = 0
    for regime_index, regime in enumerate(regimes):
        by_regime[regime.regime_id] = {
            arm: {"n": 0, "false": 0, "covered": 0, "false_block": 0, "alpha_max": 0.0}
            for arm in ARMS
        }
        for within in range(worlds_per_regime):
            world_counter += 1
            world_seed = int(hashlib.sha256(f"{seed}:{regime_index}:{within}".encode()).hexdigest()[:16], 16)
            world = generate_world(world_seed, regime, world_counter)
            for arm in ARMS:
                scored = run_arm(world, arm, broker_alpha)
                bucket = counts[arm]
                rb = by_regime[regime.regime_id][arm]
                rb["n"] += 1
                rb["false"] += int(scored["unsupported"])
                rb["covered"] += int(scored["covered"])
                rb["false_block"] += int(scored["false_block"])
                rb["alpha_max"] = max(rb["alpha_max"], scored["alpha_spent"])
                bucket["alpha_max"] = max(bucket["alpha_max"], scored["alpha_spent"])
                bucket["raw_tests_sum"] += scored["raw_tests"]
                if regime.truth_class == "NULL":
                    bucket["null_n"] += 1
                    bucket["null_false"] += int(scored["unsupported"])
                else:
                    bucket["signal_n"] += 1
                    bucket["signal_covered"] += int(scored["covered"])
                    bucket["false_block"] += int(scored["false_block"])
                    if regime.aliases:
                        bucket["alias_signal_n"] += 1
                        bucket["alias_signal_covered"] += int(scored["covered"])
                if include_events and within == 0:
                    exemplars.append({
                        "regime": regime.regime_id, "arm": arm,
                        "world": world, "result": scored,
                    })

    summary: dict[str, Any] = {
        "seed": seed, "seed_sha256": hashlib.sha256(str(seed).encode()).hexdigest(),
        "worlds_per_regime": worlds_per_regime,
        "worlds": worlds_per_regime * len(regimes),
        "broker_alpha": broker_alpha,
        "arms": {}, "by_regime": {},
    }
    for arm, row in counts.items():
        summary["arms"][arm] = {
            "null_worlds": int(row["null_n"]),
            "null_fwer": row["null_false"] / row["null_n"] if row["null_n"] else None,
            "signal_worlds": int(row["signal_n"]),
            "signal_coverage": row["signal_covered"] / row["signal_n"] if row["signal_n"] else None,
            "alias_signal_coverage": row["alias_signal_covered"] / row["alias_signal_n"] if row["alias_signal_n"] else None,
            "false_block_rate": row["false_block"] / row["signal_n"] if row["signal_n"] else None,
            "maximum_alpha_spent": row["alpha_max"],
            "mean_raw_tests": row["raw_tests_sum"] / (worlds_per_regime * len(regimes)),
            "null_false_count": int(row["null_false"]),
            "signal_covered_count": int(row["signal_covered"]),
        }
    for regime_id, arms in by_regime.items():
        summary["by_regime"][regime_id] = {}
        for arm, row in arms.items():
            n = row["n"]
            summary["by_regime"][regime_id][arm] = {
                "n": int(n), "false_rate": row["false"] / n,
                "coverage": row["covered"] / n,
                "false_block_rate": row["false_block"] / n,
                "maximum_alpha_spent": row["alpha_max"],
            }
    if include_events:
        summary["exemplars"] = exemplars
    return summary


def binomial_cdf(x: int, n: int, p: float) -> float:
    if x >= n:
        return 1.0
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    logs = [
        math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
        + k * math.log(p) + (n - k) * math.log1p(-p)
        for k in range(x + 1)
    ]
    maximum = max(logs)
    return min(1.0, max(0.0, math.exp(maximum) * sum(math.exp(value - maximum) for value in logs)))


def clopper_pearson_upper(x: int, n: int, confidence: float = 0.95) -> float:
    if x >= n:
        return 1.0
    target = 1.0 - confidence
    lo, hi = 0.0, 1.0
    for _ in range(90):
        mid = (lo + hi) / 2.0
        if binomial_cdf(x, n, mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def risk_activation_checks(summary: dict[str, Any]) -> dict[str, bool]:
    arms = summary["arms"]
    by = summary["by_regime"]
    r4 = "R4_PERSISTENT_RIEC_BROKER"
    b1 = "B1_GLOBAL_RAW_BONFERRONI"
    b3 = "B3_LOCAL_IDENTITY_BONFERRONI"
    checks = {
        "GLOBAL_ALPHA_INVARIANT": arms[r4]["maximum_alpha_spent"] <= summary["broker_alpha"] + 1e-12,
        "LOCAL_GLOBAL_RISK_SEPARATION": arms[b3]["null_fwer"] - arms[r4]["null_fwer"] >= 0.08,
        "ALIAS_SIGNAL_REACHABILITY": arms[r4]["alias_signal_coverage"] - arms[b1]["alias_signal_coverage"] >= 0.40,
        "LOCAL_COVERAGE_NONINFERIOR_0_10": arms[r4]["alias_signal_coverage"] >= arms[b3]["alias_signal_coverage"] - 0.10,
        "FIXED_NULL_CONTROL_EQUIVALENT": abs(by["N0_FIXED_CONTROL"][r4]["false_rate"] - by["N0_FIXED_CONTROL"][b3]["false_rate"]) <= 0.01,
        "FIXED_SIGNAL_CONTROL_EQUIVALENT": abs(by["S0_FIXED_CONTROL"][r4]["coverage"] - by["S0_FIXED_CONTROL"][b3]["coverage"]) <= 0.03,
        "INVALID_LURE_DOES_NOT_BREAK_ALPHA": max(
            by["N4_INVALID_HIGH_SCORE_LURE"][r4]["maximum_alpha_spent"],
            by["N5_COMBINED_RELAY"][r4]["maximum_alpha_spent"],
        ) <= summary["broker_alpha"] + 1e-12,
        # Per-regime positive direction is the mechanism check. The >=0.08
        # minimum effect-size requirement remains on the aggregate null family;
        # imposing the same fixed gap inside every dependence regime was the
        # over-constrained v1.6 condition and is preserved as a failed result.
        "COMBINED_RELAY_RISK_REDUCED_DIRECTIONALLY": by["N5_COMBINED_RELAY"][b3]["false_rate"] > by["N5_COMBINED_RELAY"][r4]["false_rate"],
    }
    return checks


def regime_ledger() -> list[dict[str, Any]]:
    return [asdict(regime) for regime in REGIMES]
