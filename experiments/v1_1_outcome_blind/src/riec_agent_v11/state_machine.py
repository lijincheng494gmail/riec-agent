"""Irreversible protected-evidence access state machine."""

from __future__ import annotations

from enum import Enum


class ProtectedEvidenceState(str, Enum):
    SEALED = "SEALED"
    Q_REGISTERED = "Q_REGISTERED"
    Q_ACTIVE = "Q_ACTIVE"
    Q_EXHAUSTED = "Q_EXHAUSTED"
    C_CANDIDATE_FROZEN = "C_CANDIDATE_FROZEN"
    C_BATCH_FROZEN = "C_BATCH_FROZEN"
    C_RELEASED = "C_RELEASED"
    C_CONSUMED = "C_CONSUMED"
    CONTAMINATED = "CONTAMINATED"
    INVALID = "INVALID"


class AccessEvent(str, Enum):
    REGISTER_Q = "REGISTER_Q"
    QUERY_Q = "QUERY_Q"
    EXHAUST_Q = "EXHAUST_Q"
    FREEZE_CANDIDATE = "FREEZE_CANDIDATE"
    FREEZE_BATCH = "FREEZE_BATCH"
    RELEASE_C = "RELEASE_C"
    CONSUME_C = "CONSUME_C"
    CONTAMINATE = "CONTAMINATE"
    INVALIDATE = "INVALIDATE"


class InvalidTransition(ValueError):
    pass


_ALLOWED = {
    (ProtectedEvidenceState.SEALED, AccessEvent.REGISTER_Q): ProtectedEvidenceState.Q_REGISTERED,
    (ProtectedEvidenceState.Q_REGISTERED, AccessEvent.QUERY_Q): ProtectedEvidenceState.Q_ACTIVE,
    (ProtectedEvidenceState.Q_ACTIVE, AccessEvent.QUERY_Q): ProtectedEvidenceState.Q_ACTIVE,
    (ProtectedEvidenceState.Q_ACTIVE, AccessEvent.EXHAUST_Q): ProtectedEvidenceState.Q_EXHAUSTED,
    (ProtectedEvidenceState.SEALED, AccessEvent.FREEZE_CANDIDATE): ProtectedEvidenceState.C_CANDIDATE_FROZEN,
    (ProtectedEvidenceState.C_CANDIDATE_FROZEN, AccessEvent.FREEZE_BATCH): ProtectedEvidenceState.C_BATCH_FROZEN,
    (ProtectedEvidenceState.C_BATCH_FROZEN, AccessEvent.RELEASE_C): ProtectedEvidenceState.C_RELEASED,
    (ProtectedEvidenceState.C_RELEASED, AccessEvent.CONSUME_C): ProtectedEvidenceState.C_CONSUMED,
}


def transition(state: ProtectedEvidenceState, event: AccessEvent) -> ProtectedEvidenceState:
    if event is AccessEvent.CONTAMINATE and state not in {
        ProtectedEvidenceState.CONTAMINATED,
        ProtectedEvidenceState.INVALID,
    }:
        return ProtectedEvidenceState.CONTAMINATED
    if event is AccessEvent.INVALIDATE and state not in {
        ProtectedEvidenceState.CONTAMINATED,
        ProtectedEvidenceState.INVALID,
    }:
        return ProtectedEvidenceState.INVALID
    try:
        return _ALLOWED[(state, event)]
    except KeyError as exc:
        raise InvalidTransition(f"forbidden transition: {state.value} + {event.value}") from exc


def permitted_transitions() -> dict[tuple[ProtectedEvidenceState, AccessEvent], ProtectedEvidenceState]:
    return dict(_ALLOWED)
