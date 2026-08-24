"""Non-compensatory authority projection for the v1.1 design model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum


class AuthorityTier(IntEnum):
    T0_DIAGNOSTIC = 0
    T1_EXPLORATORY = 1
    T2_QUALIFIED = 2
    T3_CONFIRMATORY = 3
    T4_REPLICATED = 4


class CoreStatus(str, Enum):
    PASS = "PASS"
    WARN_ELIGIBLE = "WARN_ELIGIBLE"
    WARN_INELIGIBLE = "WARN_INELIGIBLE"
    FAIL = "FAIL"
    NOT_EVALUABLE = "NOT_EVALUABLE"


class EvidenceState(str, Enum):
    D_ONLY = "D_ONLY"
    Q_ACTIVE = "Q_ACTIVE"
    Q_EXHAUSTED = "Q_EXHAUSTED"
    C_BATCH_FROZEN = "C_BATCH_FROZEN"
    C_RELEASED = "C_RELEASED"
    C_CONSUMED = "C_CONSUMED"
    CONTAMINATED = "CONTAMINATED"
    INVALID = "INVALID"
    R_RELEASED = "R_RELEASED"


@dataclass(frozen=True)
class AuthorityContext:
    core_status: CoreStatus = CoreStatus.PASS
    lineage_complete: bool = True
    identity_valid: bool = True
    evidence_state: EvidenceState = EvidenceState.D_ONLY
    qualification_passed: bool = False
    qualification_controller_valid: bool = True
    q_queries: int = 0
    final_route_frozen: bool = False
    final_claim_batch_frozen: bool = False
    final_claim_count: int = 1
    final_multiplicity_valid: bool = True
    confirmation_release_count: int = 0
    confirmation_passed: bool = False
    practical_threshold_passed: bool = False
    confirmation_used_for_selection: bool = False
    missingness_valid: bool = True
    replication_passed: bool = False


def project_authority(context: AuthorityContext) -> AuthorityTier:
    """Return the maximum claim tier permitted by every independent dimension."""

    if context.core_status not in {CoreStatus.PASS, CoreStatus.WARN_ELIGIBLE}:
        return AuthorityTier.T0_DIAGNOSTIC
    if not context.identity_valid or context.evidence_state is EvidenceState.INVALID:
        return AuthorityTier.T0_DIAGNOSTIC

    tier = AuthorityTier.T1_EXPLORATORY
    if not context.lineage_complete:
        return tier

    q_valid = (
        context.qualification_passed
        and context.qualification_controller_valid
        and context.q_queries >= 1
    )
    if q_valid:
        tier = AuthorityTier.T2_QUALIFIED

    if context.evidence_state is EvidenceState.CONTAMINATED:
        return tier

    confirmation_valid = all(
        (
            context.evidence_state in {EvidenceState.C_RELEASED, EvidenceState.C_CONSUMED, EvidenceState.R_RELEASED},
            context.final_route_frozen,
            context.final_claim_batch_frozen,
            context.final_claim_count >= 1,
            context.final_multiplicity_valid,
            context.confirmation_release_count == 1,
            context.confirmation_passed,
            context.practical_threshold_passed,
            not context.confirmation_used_for_selection,
            context.missingness_valid,
        )
    )
    if confirmation_valid:
        tier = AuthorityTier.T3_CONFIRMATORY

    if (
        tier is AuthorityTier.T3_CONFIRMATORY
        and context.evidence_state is EvidenceState.R_RELEASED
        and context.replication_passed
    ):
        tier = AuthorityTier.T4_REPLICATED
    return tier

