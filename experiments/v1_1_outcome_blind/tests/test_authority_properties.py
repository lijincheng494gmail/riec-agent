from __future__ import annotations

from dataclasses import replace
from itertools import product
import unittest

from riec_agent_v11.authority import (
    AuthorityContext,
    AuthorityTier,
    CoreStatus,
    EvidenceState,
    project_authority,
)


def valid_confirmation() -> AuthorityContext:
    return AuthorityContext(
        core_status=CoreStatus.PASS,
        lineage_complete=True,
        identity_valid=True,
        evidence_state=EvidenceState.C_RELEASED,
        qualification_passed=True,
        qualification_controller_valid=True,
        q_queries=1,
        final_route_frozen=True,
        final_claim_batch_frozen=True,
        final_claim_count=1,
        final_multiplicity_valid=True,
        confirmation_release_count=1,
        confirmation_passed=True,
        practical_threshold_passed=True,
        confirmation_used_for_selection=False,
        missingness_valid=True,
    )


class AuthorityPropertyTests(unittest.TestCase):
    def test_development_only_is_exploratory(self) -> None:
        self.assertEqual(project_authority(AuthorityContext()), AuthorityTier.T1_EXPLORATORY)

    def test_core_fail_is_noncompensatory(self) -> None:
        baseline = valid_confirmation()
        for status in (CoreStatus.FAIL, CoreStatus.NOT_EVALUABLE, CoreStatus.WARN_INELIGIBLE):
            self.assertEqual(
                project_authority(replace(baseline, core_status=status)),
                AuthorityTier.T0_DIAGNOSTIC,
            )

    def test_identity_invalid_is_noncompensatory(self) -> None:
        self.assertEqual(
            project_authority(replace(valid_confirmation(), identity_valid=False)),
            AuthorityTier.T0_DIAGNOSTIC,
        )

    def test_incomplete_lineage_caps_at_exploratory(self) -> None:
        self.assertEqual(
            project_authority(replace(valid_confirmation(), lineage_complete=False)),
            AuthorityTier.T1_EXPLORATORY,
        )

    def test_valid_qualification_is_t2(self) -> None:
        context = AuthorityContext(
            evidence_state=EvidenceState.Q_ACTIVE,
            qualification_passed=True,
            qualification_controller_valid=True,
            q_queries=3,
        )
        self.assertEqual(project_authority(context), AuthorityTier.T2_QUALIFIED)

    def test_optional_stopping_without_controller_is_exploratory(self) -> None:
        context = AuthorityContext(
            evidence_state=EvidenceState.Q_ACTIVE,
            qualification_passed=True,
            qualification_controller_valid=False,
            q_queries=10,
        )
        self.assertEqual(project_authority(context), AuthorityTier.T1_EXPLORATORY)

    def test_contaminated_c_retains_independent_valid_q_only(self) -> None:
        with_q = replace(
            valid_confirmation(),
            evidence_state=EvidenceState.CONTAMINATED,
            confirmation_passed=True,
        )
        without_q = replace(with_q, qualification_passed=False, q_queries=0)
        self.assertEqual(project_authority(with_q), AuthorityTier.T2_QUALIFIED)
        self.assertEqual(project_authority(without_q), AuthorityTier.T1_EXPLORATORY)

    def test_valid_confirmation_is_t3(self) -> None:
        self.assertEqual(project_authority(valid_confirmation()), AuthorityTier.T3_CONFIRMATORY)

    def test_confirmation_used_for_selection_is_not_t3(self) -> None:
        context = replace(valid_confirmation(), confirmation_used_for_selection=True)
        self.assertEqual(project_authority(context), AuthorityTier.T2_QUALIFIED)

    def test_uncontrolled_multiple_final_claims_are_not_t3(self) -> None:
        context = replace(valid_confirmation(), final_claim_count=20, final_multiplicity_valid=False)
        self.assertEqual(project_authority(context), AuthorityTier.T2_QUALIFIED)

    def test_invalid_missingness_is_not_t3(self) -> None:
        context = replace(valid_confirmation(), missingness_valid=False)
        self.assertEqual(project_authority(context), AuthorityTier.T2_QUALIFIED)

    def test_practical_threshold_is_required(self) -> None:
        context = replace(valid_confirmation(), practical_threshold_passed=False)
        self.assertEqual(project_authority(context), AuthorityTier.T2_QUALIFIED)

    def test_replication_requires_new_r_state(self) -> None:
        c_context = replace(valid_confirmation(), replication_passed=True)
        r_context = replace(c_context, evidence_state=EvidenceState.R_RELEASED)
        self.assertEqual(project_authority(c_context), AuthorityTier.T3_CONFIRMATORY)
        self.assertEqual(project_authority(r_context), AuthorityTier.T4_REPLICATED)

    def test_one_shot_authority_is_invariant_to_development_search_count(self) -> None:
        # Development search count is deliberately absent from authority projection.
        # It belongs in the audit ledger, not the one-shot alpha denominator.
        expected = project_authority(valid_confirmation())
        for _development_routes in (1, 10, 100, 1000, 1000000):
            self.assertEqual(project_authority(valid_confirmation()), expected)

    def test_exhaustive_core_and_identity_noncompensation(self) -> None:
        baseline = valid_confirmation()
        for status, identity, lineage, multiplicity in product(
            list(CoreStatus), (False, True), (False, True), (False, True)
        ):
            context = replace(
                baseline,
                core_status=status,
                identity_valid=identity,
                lineage_complete=lineage,
                final_multiplicity_valid=multiplicity,
            )
            tier = project_authority(context)
            if status not in {CoreStatus.PASS, CoreStatus.WARN_ELIGIBLE} or not identity:
                self.assertEqual(tier, AuthorityTier.T0_DIAGNOSTIC)
            elif not lineage:
                self.assertLessEqual(tier, AuthorityTier.T1_EXPLORATORY)

    def test_single_dimension_degradation_never_increases_authority(self) -> None:
        baseline = valid_confirmation()
        baseline_tier = project_authority(baseline)
        degraded = [
            replace(baseline, core_status=CoreStatus.FAIL),
            replace(baseline, lineage_complete=False),
            replace(baseline, identity_valid=False),
            replace(baseline, evidence_state=EvidenceState.CONTAMINATED),
            replace(baseline, qualification_controller_valid=False),
            replace(baseline, final_route_frozen=False),
            replace(baseline, final_claim_batch_frozen=False),
            replace(baseline, final_multiplicity_valid=False),
            replace(baseline, confirmation_release_count=2),
            replace(baseline, confirmation_passed=False),
            replace(baseline, practical_threshold_passed=False),
            replace(baseline, confirmation_used_for_selection=True),
            replace(baseline, missingness_valid=False),
        ]
        for context in degraded:
            self.assertLessEqual(project_authority(context), baseline_tier)


if __name__ == "__main__":
    unittest.main()

