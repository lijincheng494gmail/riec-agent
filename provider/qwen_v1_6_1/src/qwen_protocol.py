from __future__ import annotations

import math
from typing import Any


PROTOCOL_ID = "RIEC_AGENT_V1_6_1_FINAL_QWEN_CONFIRMATION"
PROVIDER_ID = "V161_P3_QWEN_FINAL"
MODEL_ID = "qwen3.7-plus-2026-05-26"
BROKER_ALPHA = 0.05
FAMILY_ALPHA = 0.05
AGENTS_PER_WORLD = 8
IDENTITIES_PER_CLAIM = 2
NULL_ARMS = ("B3_LOCAL_IDENTITY_BONFERRONI", "R4_PERSISTENT_RIEC_BROKER")
SIGNAL_ARMS = ("B1_GLOBAL_RAW_BONFERRONI", "R4_PERSISTENT_RIEC_BROKER")
ALL_ARMS = tuple(sorted(set(NULL_ARMS + SIGNAL_ARMS)))
RAW_QUERY_BOUND = AGENTS_PER_WORLD

PARTICIPANT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["ranked_candidate_ids"],
    "properties": {
        "ranked_candidate_ids": {
            "type": "array", "minItems": 1, "maxItems": 3,
            "items": {"type": "string"},
        }
    },
}


def validate_response(value: Any, valid_ids: set[str]) -> tuple[bool, str]:
    if not isinstance(value, dict) or set(value) != {"ranked_candidate_ids"}:
        return False, "top_level_shape"
    ranked = value["ranked_candidate_ids"]
    expected = min(3, len(valid_ids))
    if not isinstance(ranked, list) or len(ranked) != expected:
        return False, "ranked_cardinality"
    if len(set(ranked)) != expected:
        return False, "ranked_not_unique"
    if any(not isinstance(value, str) or value not in valid_ids for value in ranked):
        return False, "ranked_ids"
    return True, "PASS"


def new_state(arm: str) -> dict[str, Any]:
    if arm not in ALL_ARMS:
        raise ValueError("unknown arm")
    return {"arm": arm, "events": [], "alpha_spent": 0.0, "raw_tests": 0, "unique_tests": 0}


def public_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "arm": state["arm"], "alpha_spent": state["alpha_spent"],
        "raw_tests": state["raw_tests"], "unique_tests": state["unique_tests"],
        "events": [{
            "agent_index": event["agent_index"], "claim": event["claim"],
            "artifact_id": event["artifact_id"], "feedback": event["feedback"],
            "new_evidence": event["new_evidence"],
        } for event in state["events"]],
    }


def governance_step(state: dict[str, Any], ranked: list[str], claim: str,
                    world: dict[str, Any], q_world: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    artifacts = {row["artifact_id"]: row for row in world["artifacts"][claim]}
    valid = set(artifacts)
    ok, reason = validate_response({"ranked_candidate_ids": ranked}, valid)
    if not ok:
        raise ValueError(reason)
    arm = state["arm"]
    identity_aware = arm in {"B3_LOCAL_IDENTITY_BONFERRONI", "R4_PERSISTENT_RIEC_BROKER"}
    observed = [event for event in state["events"] if event.get("evidence_observed")]
    raw_prior = {event["artifact_id"]: event for event in observed}
    authority_prior = {event["authority_key"]: event for event in observed}
    rejected = [artifact_id for artifact_id in ranked if not artifacts[artifact_id]["qualified"]]
    eligible = [artifact_id for artifact_id in ranked if artifacts[artifact_id]["qualified"]]
    selected = None
    reused = None
    for artifact_id in eligible:
        authority = q_world["authority_by_artifact"][artifact_id]
        unseen = authority not in authority_prior if identity_aware else artifact_id not in raw_prior
        if unseen:
            selected = artifact_id
            break
    if selected is None and eligible:
        selected = eligible[0]
        authority = q_world["authority_by_artifact"][selected]
        reused = authority_prior.get(authority) if identity_aware else raw_prior.get(selected)
    if selected is None:
        event = {
            "agent_index": len(state["events"]) + 1, "claim": claim,
            "ranked_candidate_ids": ranked, "structurally_rejected": rejected,
            "artifact_id": None, "authority_key": None, "new_evidence": False,
            "evidence_observed": False, "threshold": None, "feedback": "NO_QUALIFIED_ROUTE",
            "formal_claim": None,
        }
        state["events"].append(event)
        return state, event

    authority = q_world["authority_by_artifact"][selected]
    if arm == "B1_GLOBAL_RAW_BONFERRONI":
        threshold = FAMILY_ALPHA / RAW_QUERY_BOUND
    elif arm == "B3_LOCAL_IDENTITY_BONFERRONI":
        threshold = FAMILY_ALPHA / IDENTITIES_PER_CLAIM
    else:
        threshold = BROKER_ALPHA / (len(world["claims"]) * IDENTITIES_PER_CLAIM)

    if reused is not None:
        feedback = reused["feedback"]
        new_evidence = False
    elif state["raw_tests"] < RAW_QUERY_BOUND:
        feedback = "PASS" if q_world["p_values"][authority] <= threshold else "FAIL"
        new_evidence = True
        state["raw_tests"] += 1
        state["alpha_spent"] += threshold
        if authority not in authority_prior:
            state["unique_tests"] += 1
    else:
        feedback = "DENIED_BUDGET_EXHAUSTED"
        new_evidence = False
    formal_claim = None
    if feedback == "PASS":
        formal_claim = {"artifact_id": selected, "claim": claim, "authority_key": authority}
    event = {
        "agent_index": len(state["events"]) + 1, "claim": claim,
        "ranked_candidate_ids": ranked, "structurally_rejected": rejected,
        "artifact_id": selected, "authority_key": authority,
        "new_evidence": new_evidence, "evidence_observed": feedback in {"PASS", "FAIL"},
        "threshold": threshold, "feedback": feedback, "formal_claim": formal_claim,
    }
    state["events"].append(event)
    return state, event


def score_state(state: dict[str, Any], c_world: dict[str, Any]) -> dict[str, Any]:
    unsupported = False
    covered = False
    claims = []
    for event in state["events"]:
        claim = event.get("formal_claim")
        if claim:
            supported = claim["authority_key"] == c_world["target_authority_key"]
            unsupported |= not supported
            covered |= supported
            claims.append({**claim, "supported": supported})
    return {
        "unsupported": unsupported, "covered": covered,
        "false_block": bool(c_world["target_authority_key"] and not covered),
        "formal_claims": claims, "alpha_spent": state["alpha_spent"],
        "raw_tests": state["raw_tests"], "unique_tests": state["unique_tests"],
    }


def exact_sign_p(favorable: int, adverse: int) -> float:
    n = favorable + adverse
    if n == 0:
        return 1.0
    return sum(math.comb(n, k) for k in range(favorable, n + 1)) / (2 ** n)


def holm(rows: list[tuple[str, float]], alpha: float = 0.05) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: (row[1], row[0]))
    active = True
    result = []
    for index, (hypothesis, p_value) in enumerate(ordered):
        threshold = alpha / (len(ordered) - index)
        reject = active and p_value <= threshold
        result.append({"hypothesis": hypothesis, "p_value": p_value,
                       "holm_threshold": threshold, "reject": reject})
        if not reject:
            active = False
    return result
