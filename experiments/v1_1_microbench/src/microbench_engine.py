"""Deterministic targeted-risk adjudicator for RIEC-Agent v1.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Any


EXPERIMENTS_DIR = Path(__file__).resolve().parents[2]
BOUND_VALIDATION_SRC = EXPERIMENTS_DIR / "v1_1_outcome_blind/src"
sys.path.insert(0, str(BOUND_VALIDATION_SRC))

from riec_agent_v11.authority import (  # noqa: E402
    AuthorityContext,
    AuthorityTier,
    CoreStatus,
    EvidenceState,
    project_authority,
)
from riec_agent_v11.multiplicity import holm_rejections  # noqa: E402


DEFAULT_FACTS: dict[str, Any] = {
    "alpha": 0.05,
    "requested_tier": 3,
    "evidence_mode": "C",
    "core_g0_registered": True,
    "core_g1_estimand_aligned": True,
    "core_g2_identity_valid": True,
    "core_g3_deployment_aligned": True,
    "core_g4_support_sufficient": True,
    "core_g5_uncertainty_valid": True,
    "core_g6_domain_admissible": True,
    "broker_mediated": True,
    "lineage_complete": True,
    "global_ledger": True,
    "agent_count": 1,
    "claimed_independent_replications": 1,
    "unique_evidence_identities": 1,
    "claim_family_registered": True,
    "semantic_reset": False,
    "development_routes": 10,
    "development_ceiling": 1000,
    "q_queries": 1,
    "q_budget": 20,
    "q_controller": "SINGLE",
    "q_p_values": [0.01],
    "q_feedback_registered": True,
    "final_route_frozen": True,
    "final_batch_frozen": True,
    "final_claim_count": 1,
    "final_controller": "SINGLE",
    "confirmation_p_values": [0.01],
    "target_claim_index": 0,
    "c_release_count": 1,
    "c_contaminated": False,
    "c_used_for_selection": False,
    "final_effect_source": "C",
    "confirmation_ci_low": 0.10,
    "minimum_effect": 0.08,
    "missingness_valid": True,
    "version_mutated_postfreeze": False,
}


MUTANTS = {
    "M_IGNORE_G0", "M_IGNORE_G1", "M_IGNORE_G2", "M_IGNORE_G3",
    "M_IGNORE_G4", "M_IGNORE_G5", "M_IGNORE_G6",
    "M_IGNORE_BROKER", "M_IGNORE_LINEAGE", "M_PER_AGENT_BUDGET_RESET",
    "M_COUNT_AGENT_CONSENSUS_AS_REPLICATION", "M_IGNORE_Q_BUDGET",
    "M_IGNORE_FEEDBACK_REGISTRATION", "M_IGNORE_SEQUENTIAL_VALIDITY",
    "M_IGNORE_FINAL_MULTIPLICITY", "M_ALLOW_SEMANTIC_RESET",
    "M_ALLOW_C_REUSE", "M_ALLOW_CONTAMINATED_C", "M_ALLOW_C_SELECTION",
    "M_IGNORE_PRACTICAL_THRESHOLD", "M_IGNORE_MISSINGNESS",
    "M_USE_DEVELOPMENT_EFFECT", "M_ALLOW_VERSION_MUTATION",
    "M_PENALIZE_DEVELOPMENT_SEARCH",
}


@dataclass(frozen=True)
class Evaluation:
    authority: str
    action: str
    core_failures: tuple[str, ...]
    triggered_rules: tuple[str, ...]
    qualification_passed: bool
    statistical_confirmation_passed: bool
    practical_threshold_passed: bool

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["core_failures"] = list(self.core_failures)
        result["triggered_rules"] = list(self.triggered_rules)
        return result


def _facts(overrides: dict[str, Any]) -> dict[str, Any]:
    facts = dict(DEFAULT_FACTS)
    facts.update(overrides)
    return facts


def _core_failures(facts: dict[str, Any], mutant: str | None) -> list[str]:
    mapping = [
        ("G0", "core_g0_registered"),
        ("G1", "core_g1_estimand_aligned"),
        ("G2", "core_g2_identity_valid"),
        ("G3", "core_g3_deployment_aligned"),
        ("G4", "core_g4_support_sufficient"),
        ("G5", "core_g5_uncertainty_valid"),
        ("G6", "core_g6_domain_admissible"),
    ]
    return [gate for gate, field in mapping if not facts[field] and mutant != f"M_IGNORE_{gate}"]


def _qualification(facts: dict[str, Any], mutant: str | None) -> tuple[bool, bool]:
    q_queries = int(facts["q_queries"])
    controller = facts["q_controller"]
    p_values = [float(value) for value in facts["q_p_values"]]
    if q_queries <= 1:
        return True, min(p_values) <= facts["alpha"]
    if controller == "GLOBAL_BONFERRONI":
        return True, min(p_values) <= facts["alpha"] / q_queries
    if mutant == "M_IGNORE_SEQUENTIAL_VALIDITY":
        return True, min(p_values) <= facts["alpha"]
    return False, False


def _confirmation(facts: dict[str, Any], mutant: str | None) -> tuple[bool, bool, bool]:
    p_values = [float(value) for value in facts["confirmation_p_values"]]
    claim_count = int(facts["final_claim_count"])
    if len(p_values) != claim_count:
        raise ValueError("confirmation_p_values length must equal final_claim_count")
    target = int(facts["target_claim_index"])
    if claim_count == 1:
        multiplicity_valid = True
        rejected = p_values[target] <= facts["alpha"]
    elif facts["final_controller"] == "HOLM":
        multiplicity_valid = True
        rejected = holm_rejections(p_values, facts["alpha"])[target]
    else:
        multiplicity_valid = mutant == "M_IGNORE_FINAL_MULTIPLICITY"
        rejected = p_values[target] <= facts["alpha"]
    practical = float(facts["confirmation_ci_low"]) >= float(facts["minimum_effect"])
    if mutant == "M_IGNORE_PRACTICAL_THRESHOLD":
        practical = True
    return multiplicity_valid, rejected, practical


def evaluate_case(case: dict[str, Any], mutant: str | None = None) -> Evaluation:
    if mutant is not None and mutant not in MUTANTS:
        raise ValueError(f"unknown mutant: {mutant}")
    facts = _facts(case.get("overrides", {}))
    core_failures = _core_failures(facts, mutant)
    q_controller_valid, qualification_passed = _qualification(facts, mutant)
    multiplicity_valid, statistical_passed, practical_passed = _confirmation(facts, mutant)
    rules: set[str] = set()

    if "G0" in core_failures:
        rules.add("RA-001")
    if not facts["broker_mediated"] and mutant != "M_IGNORE_BROKER":
        rules.add("RA-002")
    if not facts["lineage_complete"] and mutant != "M_IGNORE_LINEAGE":
        rules.add("RA-003")
    if not facts["global_ledger"] and mutant != "M_PER_AGENT_BUDGET_RESET":
        rules.add("RA-004")
    if "G2" in core_failures:
        rules.add("RA-005")
    consensus_violation = facts["claimed_independent_replications"] > facts["unique_evidence_identities"]
    if consensus_violation and mutant != "M_COUNT_AGENT_CONSENSUS_AS_REPLICATION":
        rules.add("RA-006")
    if not facts["claim_family_registered"]:
        rules.add("RA-007")
    if facts["semantic_reset"] and mutant != "M_ALLOW_SEMANTIC_RESET":
        rules.add("RA-008")
    if facts["development_routes"] > facts["development_ceiling"]:
        rules.add("RA-009")
    if facts["q_queries"] > facts["q_budget"] and mutant != "M_IGNORE_Q_BUDGET":
        rules.add("RA-010")
    if not facts["q_feedback_registered"] and mutant != "M_IGNORE_FEEDBACK_REGISTRATION":
        rules.add("RA-011")
    if facts["requested_tier"] >= 3 and not facts["final_batch_frozen"]:
        rules.add("RA-012")
    if facts["requested_tier"] >= 3 and facts["c_release_count"] != 1 and mutant != "M_ALLOW_C_REUSE":
        rules.add("RA-013")
    if facts["requested_tier"] >= 3 and facts["c_contaminated"] and mutant != "M_ALLOW_CONTAMINATED_C":
        rules.add("RA-014")
    if facts["requested_tier"] >= 3 and facts["final_claim_count"] > 1 and not multiplicity_valid:
        rules.add("RA-016")
    if facts["q_queries"] > 1 and not q_controller_valid:
        rules.add("RA-017")
    if core_failures:
        rules.add("RA-019")
    if any(gate in core_failures for gate in ("G1", "G3", "G4")) and statistical_passed:
        rules.add("RA-020")
    selection_violation = facts["c_used_for_selection"] and mutant != "M_ALLOW_C_SELECTION"
    effect_source_violation = facts["final_effect_source"] != "C" and mutant != "M_USE_DEVELOPMENT_EFFECT"
    if selection_violation or effect_source_violation:
        rules.add("RA-022")
    if facts["requested_tier"] >= 3 and not practical_passed:
        rules.add("RA-023")
    if not facts["missingness_valid"] and mutant != "M_IGNORE_MISSINGNESS":
        rules.add("RA-025")
    if facts["version_mutated_postfreeze"] and mutant != "M_ALLOW_VERSION_MUTATION":
        rules.add("RA-029")

    if core_failures:
        core_status = CoreStatus.FAIL
    else:
        core_status = CoreStatus.PASS

    if facts["evidence_mode"] == "Q":
        evidence_state = EvidenceState.Q_ACTIVE
    elif facts["c_contaminated"] and mutant != "M_ALLOW_CONTAMINATED_C":
        evidence_state = EvidenceState.CONTAMINATED
    elif facts["evidence_mode"] == "R":
        evidence_state = EvidenceState.R_RELEASED
    else:
        evidence_state = EvidenceState.C_RELEASED

    context = AuthorityContext(
        core_status=core_status,
        lineage_complete=facts["lineage_complete"] or mutant == "M_IGNORE_LINEAGE",
        identity_valid="G2" not in core_failures,
        evidence_state=evidence_state,
        qualification_passed=qualification_passed,
        qualification_controller_valid=q_controller_valid,
        q_queries=int(facts["q_queries"]),
        final_route_frozen=bool(facts["final_route_frozen"]),
        final_claim_batch_frozen=bool(facts["final_batch_frozen"]),
        final_claim_count=int(facts["final_claim_count"]),
        final_multiplicity_valid=multiplicity_valid,
        confirmation_release_count=(1 if mutant == "M_ALLOW_C_REUSE" else int(facts["c_release_count"])),
        confirmation_passed=statistical_passed,
        practical_threshold_passed=practical_passed,
        confirmation_used_for_selection=selection_violation or effect_source_violation,
        missingness_valid=bool(facts["missingness_valid"] or mutant == "M_IGNORE_MISSINGNESS"),
        replication_passed=facts["evidence_mode"] == "R",
    )
    tier = project_authority(context)

    caps = {
        "RA-002": AuthorityTier.T1_EXPLORATORY,
        "RA-003": AuthorityTier.T1_EXPLORATORY,
        "RA-004": AuthorityTier.T1_EXPLORATORY,
        "RA-006": AuthorityTier.T2_QUALIFIED,
        "RA-007": AuthorityTier.T1_EXPLORATORY,
        "RA-008": AuthorityTier.T1_EXPLORATORY,
        "RA-009": AuthorityTier.T1_EXPLORATORY,
        "RA-010": AuthorityTier.T1_EXPLORATORY,
        "RA-011": AuthorityTier.T1_EXPLORATORY,
        "RA-012": AuthorityTier.T2_QUALIFIED,
        "RA-013": AuthorityTier.T2_QUALIFIED,
        "RA-016": AuthorityTier.T2_QUALIFIED,
        "RA-017": AuthorityTier.T1_EXPLORATORY,
        "RA-022": AuthorityTier.T2_QUALIFIED,
        "RA-023": AuthorityTier.T2_QUALIFIED,
        "RA-025": AuthorityTier.T2_QUALIFIED,
        "RA-029": AuthorityTier.T0_DIAGNOSTIC,
    }
    for rule in rules:
        if rule in caps:
            tier = min(tier, caps[rule])

    if mutant == "M_PENALIZE_DEVELOPMENT_SEARCH" and facts["development_routes"] > 1 and tier >= AuthorityTier.T3_CONFIRMATORY:
        tier = AuthorityTier.T2_QUALIFIED

    if "RA-029" in rules:
        action = "PROTOCOL_INVALID"
    elif tier >= AuthorityTier.T3_CONFIRMATORY:
        action = "CONFIRM"
    elif tier is AuthorityTier.T2_QUALIFIED:
        action = "QUALIFY"
    elif tier is AuthorityTier.T1_EXPLORATORY:
        action = "DOWNGRADE"
    else:
        action = "DIAGNOSTIC_ONLY"

    return Evaluation(
        authority=tier.name,
        action=action,
        core_failures=tuple(core_failures),
        triggered_rules=tuple(sorted(rules)),
        qualification_passed=qualification_passed,
        statistical_confirmation_passed=statistical_passed,
        practical_threshold_passed=practical_passed,
    )


def matches_expected(evaluation: Evaluation, expected: dict[str, Any]) -> bool:
    return all((
        evaluation.authority == expected["authority"],
        evaluation.action == expected["action"],
        list(evaluation.core_failures) == expected["core_failures"],
        list(evaluation.triggered_rules) == expected["triggered_rules"],
    ))
