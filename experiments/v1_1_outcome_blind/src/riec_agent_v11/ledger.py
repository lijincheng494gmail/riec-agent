"""Global search and protected-evidence ledger."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LedgerEvent:
    agent_id: str
    session_id: str
    provider_id: str
    evidence_identity: str
    claim_family: str
    spec_hash: str
    pool: str
    information_released: bool
    query_debit: int = 0

    def __post_init__(self) -> None:
        if not all((self.agent_id, self.session_id, self.provider_id, self.evidence_identity, self.claim_family, self.spec_hash)):
            raise ValueError("ledger identities must be non-empty")
        if self.pool not in {"D", "Q", "C", "R"}:
            raise ValueError("unknown evidence pool")
        if self.query_debit < 0:
            raise ValueError("query debit cannot be negative")
        if self.information_released and self.pool in {"Q", "C", "R"} and self.query_debit < 1:
            raise ValueError("protected information release requires a positive debit")


class GlobalEvidenceLedger:
    def __init__(self) -> None:
        self._events: list[LedgerEvent] = []

    def add(self, event: LedgerEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> tuple[LedgerEvent, ...]:
        return tuple(self._events)

    def query_debit(self, evidence_identity: str, claim_family: str) -> int:
        return sum(
            event.query_debit
            for event in self._events
            if event.evidence_identity == evidence_identity and event.claim_family == claim_family
        )

    def unique_specifications(self, evidence_identity: str, claim_family: str) -> int:
        return len({
            event.spec_hash
            for event in self._events
            if event.evidence_identity == evidence_identity and event.claim_family == claim_family
        })

    def independent_evidence_count(self, claim_family: str) -> int:
        return len({event.evidence_identity for event in self._events if event.claim_family == claim_family})

    def agents(self, evidence_identity: str, claim_family: str) -> set[str]:
        return {
            event.agent_id
            for event in self._events
            if event.evidence_identity == evidence_identity and event.claim_family == claim_family
        }

