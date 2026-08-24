# Prefreeze readiness checklist

Current status: `NOT_READY_FOR_PREFREEZE`

A future RIEC-Agent v1.1 campaign may enter pre-outcome freeze only when every item below is satisfied.

## Architecture

- [ ] Core v1.0 checksum is bound and unchanged.
- [ ] Agent-layer schemas and rule versions are immutable.
- [ ] Every RA-001–RA-029 rule has executable validation or an explicitly auditable manual decision.
- [ ] Authority-tier projection passes property tests for monotonicity and non-compensation.
- [ ] Evidence-state machine rejects all forbidden reverse transitions.

## Statistical validity

- [ ] One-shot sufficiency behavior is tested.
- [ ] Sequential Q controller has a documented validity basis and simulation coverage.
- [ ] Final FWER controller is fixed.
- [ ] Minimum effects/equivalence margins are scientifically justified without provider-outcome tuning.
- [ ] R0 non-inferiority margin and power are frozen.
- [ ] Missingness bounds and completion-validity thresholds are frozen.

## Benchmark validity

- [ ] Each targeted risk has a prospective activation oracle.
- [ ] Each structural risk activates its designated Core rule in blinded microtests.
- [ ] B2 protected one-shot holdout receives no artificial disadvantage.
- [ ] B3 and B4 cleanly isolate structural-only and numerical-only mechanisms.
- [ ] B5 uses exactly unchanged Core plus the declared Agent layer.
- [ ] At least one null/control regime is included where no hybrid advantage is expected.

## Agent and evidence isolation

- [ ] All empirical access is broker-mediated.
- [ ] Global ledgers union access across agents/providers/sessions.
- [ ] Q and C evidence identities are independently committed.
- [ ] Atomic C release is tested against partial-output and error-channel leakage.
- [ ] Retry rules distinguish no-information transport failure from consumed evidence.

## Claims and governance

- [ ] Claim-family ontology is frozen.
- [ ] Primary hypotheses and FWER family are frozen.
- [ ] Falsification criteria are included in the public protocol.
- [ ] Negative, incomplete and contaminated outcomes are manifest-preserved.
- [ ] The paper claim boundary excludes universal AI-science governance and universal component necessity.

Until these items pass, this package remains a design record and must not be described as RIEC-Agent v1.1 validation.

