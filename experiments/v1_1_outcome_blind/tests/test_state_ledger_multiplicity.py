from __future__ import annotations

import unittest

from riec_agent_v11.ledger import GlobalEvidenceLedger, LedgerEvent
from riec_agent_v11.multiplicity import (
    bonferroni_rejections,
    global_query_threshold,
    holm_rejections,
)
from riec_agent_v11.state_machine import (
    AccessEvent,
    InvalidTransition,
    ProtectedEvidenceState,
    transition,
)


class StateMachineTests(unittest.TestCase):
    def test_qualification_path(self) -> None:
        state = transition(ProtectedEvidenceState.SEALED, AccessEvent.REGISTER_Q)
        state = transition(state, AccessEvent.QUERY_Q)
        state = transition(state, AccessEvent.QUERY_Q)
        state = transition(state, AccessEvent.EXHAUST_Q)
        self.assertEqual(state, ProtectedEvidenceState.Q_EXHAUSTED)

    def test_confirmation_path(self) -> None:
        state = transition(ProtectedEvidenceState.SEALED, AccessEvent.FREEZE_CANDIDATE)
        state = transition(state, AccessEvent.FREEZE_BATCH)
        state = transition(state, AccessEvent.RELEASE_C)
        state = transition(state, AccessEvent.CONSUME_C)
        self.assertEqual(state, ProtectedEvidenceState.C_CONSUMED)

    def test_no_return_to_sealed(self) -> None:
        terminal_or_open = [
            ProtectedEvidenceState.Q_ACTIVE,
            ProtectedEvidenceState.Q_EXHAUSTED,
            ProtectedEvidenceState.C_RELEASED,
            ProtectedEvidenceState.C_CONSUMED,
            ProtectedEvidenceState.CONTAMINATED,
            ProtectedEvidenceState.INVALID,
        ]
        for state in terminal_or_open:
            with self.assertRaises(InvalidTransition):
                transition(state, AccessEvent.FREEZE_CANDIDATE)

    def test_contamination_is_terminal(self) -> None:
        contaminated = transition(ProtectedEvidenceState.C_BATCH_FROZEN, AccessEvent.CONTAMINATE)
        self.assertEqual(contaminated, ProtectedEvidenceState.CONTAMINATED)
        for event in AccessEvent:
            with self.assertRaises(InvalidTransition):
                transition(contaminated, event)

    def test_partial_release_cannot_be_retried(self) -> None:
        released = transition(ProtectedEvidenceState.C_BATCH_FROZEN, AccessEvent.RELEASE_C)
        with self.assertRaises(InvalidTransition):
            transition(released, AccessEvent.RELEASE_C)


class LedgerTests(unittest.TestCase):
    @staticmethod
    def event(agent: str, spec: str, evidence: str = "E1", debit: int = 1) -> LedgerEvent:
        return LedgerEvent(
            agent_id=agent,
            session_id=f"session-{agent}-{spec}",
            provider_id=f"provider-{agent}",
            evidence_identity=evidence,
            claim_family="CF1",
            spec_hash=spec,
            pool="Q",
            information_released=True,
            query_debit=debit,
        )

    def test_multiagent_queries_union_globally(self) -> None:
        ledger = GlobalEvidenceLedger()
        for agent in ("A", "B", "C"):
            for index in range(4):
                ledger.add(self.event(agent, f"{agent}-{index}"))
        self.assertEqual(ledger.query_debit("E1", "CF1"), 12)
        self.assertEqual(ledger.unique_specifications("E1", "CF1"), 12)
        self.assertEqual(ledger.agents("E1", "CF1"), {"A", "B", "C"})

    def test_agent_split_does_not_change_total_debit(self) -> None:
        one = GlobalEvidenceLedger()
        many = GlobalEvidenceLedger()
        for index in range(20):
            one.add(self.event("A", f"s{index}"))
            many.add(self.event(f"A{index % 5}", f"s{index}"))
        self.assertEqual(one.query_debit("E1", "CF1"), many.query_debit("E1", "CF1"))
        self.assertEqual(one.unique_specifications("E1", "CF1"), many.unique_specifications("E1", "CF1"))

    def test_same_evidence_across_agents_is_one_identity(self) -> None:
        ledger = GlobalEvidenceLedger()
        ledger.add(self.event("A", "s1", "E1"))
        ledger.add(self.event("B", "s2", "E1"))
        self.assertEqual(ledger.independent_evidence_count("CF1"), 1)

    def test_new_evidence_identity_counts_once_each(self) -> None:
        ledger = GlobalEvidenceLedger()
        ledger.add(self.event("A", "s1", "E1"))
        ledger.add(self.event("B", "s2", "E2"))
        self.assertEqual(ledger.independent_evidence_count("CF1"), 2)

    def test_protected_information_requires_debit(self) -> None:
        with self.assertRaises(ValueError):
            LedgerEvent("A", "S", "P", "E", "C", "H", "Q", True, 0)


class MultiplicityTests(unittest.TestCase):
    def test_bonferroni_single_claim_is_ordinary_alpha(self) -> None:
        self.assertEqual(bonferroni_rejections([0.049], 0.05), [True])

    def test_bonferroni_multiple_claims(self) -> None:
        self.assertEqual(bonferroni_rejections([0.009, 0.011, 0.9], 0.03), [True, False, False])

    def test_holm_stepdown(self) -> None:
        self.assertEqual(holm_rejections([0.001, 0.02, 0.2], 0.05), [True, True, False])

    def test_multiplicity_validation(self) -> None:
        with self.assertRaises(ValueError):
            holm_rejections([], 0.05)
        with self.assertRaises(ValueError):
            bonferroni_rejections([1.1], 0.05)

    def test_global_query_threshold_counts_all_agents(self) -> None:
        self.assertAlmostEqual(global_query_threshold(40, 0.05), 0.00125)


if __name__ == "__main__":
    unittest.main()

