# RIEC-Agent v1.1 candidate rulebook

Status: `DESIGN_DRAFT_NOT_PREFROZEN`

## A. Registration and traceability

### RA-001 — Campaign envelope

Before agent execution, freeze the target, estimand, population, deployment world, candidate claim classes, maximum development operations, maximum protected-evidence accesses, agent roster, provider/model identifiers where available, stopping rules, missingness handling and final decision policy.

Failure consequence: maximum authority T1.

### RA-002 — Broker-mediated empirical access

Any agent eligible to contribute to T2 or higher must receive empirical outcomes only through an auditable broker. Raw protected outcomes, unrestricted filesystem access, unlogged notebooks or invisible external tools are prohibited.

Failure consequence: protected pool becomes CONTAMINATED; maximum authority T1.

### RA-003 — Complete observable lineage

Record each executed route, parent route, specification hash, evidence pool, data identity, returned feedback class, time, agent/session identity, operation debit and associated claim family. Private chain-of-thought is out of scope.

Failure consequence: incomplete lineage; maximum authority T1.

### RA-004 — Global campaign ledger

Search and evidence accounting is global across agents, prompts, seeds, sessions and providers when they operate on the same evidence identity and claim family. No per-agent reset is allowed.

Failure consequence: ledger inconsistency; maximum authority T1 until reconciled before protected access, otherwise POST_FREEZE_FORBIDDEN.

## B. Identity and claim-family accounting

### RA-005 — Evidence identity before evidence count

Independent support is counted by subject/study/experimental-unit identity, not by file, report, model, agent or effect-row count. Aliases and overlapping cohorts are one dependence group unless a registered model justifies otherwise.

Failure consequence: Core G2 FAIL or NOT_EVALUABLE; maximum authority T0 for claims requiring independence.

### RA-006 — Agent consensus is not replication

Multiple agents analyzing the same data may expand the search space but do not add independent evidence. Consensus is reported as an operational result only.

Failure consequence for misclassification: T3/T4 blocked.

### RA-007 — Claim-family registration

Every assertive claim maps to a frozen family identifier. Directional variants, discovered subgroups, alternative endpoints, metrics, time points and materially different estimands remain visible in the family graph.

Failure consequence: unregistered claim is T0/T1 only.

### RA-008 — No semantic reset

Rewording or narrowing a claim after protected feedback does not reset its family, alpha/evidence budget or contamination status. A genuinely new estimand requires a new prospective family and fresh evidence.

Failure consequence: post-feedback reformulation is exploratory only.

## C. Search budget and protected evidence

### RA-009 — Development-search freedom with a ceiling

Adaptive D-stage search is permitted up to the frozen operational ceiling. Search count, unique route count, feedback rounds, claim revisions and early stopping are disclosed. D evidence never exceeds T1 authority regardless of apparent significance.

Failure consequence for exceeding the ceiling: episode is terminal INCOMPLETE or protocol deviation; no favorable replacement run.

### RA-010 — Qualification-access budget

Q access is a finite campaign-level resource. Every query, including failed, partial, pass/fail-only and exact-score query, consumes the registered debit. Debits cannot be refunded after information release.

Failure consequence when exhausted: further protected queries are blocked; existing Q cannot become C.

### RA-011 — Minimal feedback

The Q broker returns only the information class frozen in advance: pass/fail, interval category, noisy score, or exact statistic. More informative feedback consumes at least as much access budget as less informative feedback and can never preserve more authority.

Failure consequence for unregistered feedback: Q becomes contaminated for the affected family.

### RA-012 — Final batch freeze

Before C access, freeze all final claim records together, including route hash, claim family, direction, target, estimand, unit, population, minimum effect of interest, test/interval, missingness rule, weights and multiplicity controller. C results are released only after the batch is immutable.

Failure consequence: T3 blocked.

### RA-013 — One access means one access

C may be evaluated once per frozen final batch. No route replacement, seed replacement, subgroup substitution, endpoint substitution or resubmission is permitted after any C information is released.

Failure consequence: C is CONSUMED; later variants require new evidence and a new freeze.

### RA-014 — Contamination is irreversible

Any unauthorized aggregate, row-level value, direction, rank, error message encoding outcome information, or data-dependent acceptance signal from C changes its state to CONTAMINATED. Closing the file or starting a new session does not restore it.

Failure consequence: maximum authority T2 using other valid evidence; T3 requires a fresh C identity.

## D. Multiplicity and sequential validity

### RA-015 — Development routes are not the final alpha family

When exactly one claim is frozen and tested once on untouched C, no automatic alpha division by the number of D routes is applied. D-route multiplicity is recorded as selection exposure and evaluated through C.

### RA-016 — Final-claim familywise control

When more than one final claim is tested on C, the frozen procedure must control familywise error at 0.05 using Holm, weighted Bonferroni, closed testing or a justified hierarchical gatekeeping procedure. One claim receives the full 0.05 allocation. FDR-only control cannot support T3 confirmatory language unless the claim boundary explicitly permits discovery-set rather than individual-claim authority.

Failure consequence: maximum authority T2.

### RA-017 — Sequential protected access

Adaptive/repeated Q or C access must use a valid anytime procedure such as a preregistered e-process/confidence sequence or a fully specified alpha-spending design. Optional stopping with ordinary fixed-sample p-values is invalid.

Failure consequence: maximum authority T1 for the affected numerical claim.

### RA-018 — No universal effective-search shortcut

Raw evaluations, unique specification hashes and claim-family counts are primary audit quantities. Correlation-adjusted effective search counts may be sensitivity analyses but cannot reduce conservative multiplicity obligations unless the estimator and its validity are preregistered.

## E. Structural and numerical composition

### RA-019 — Core-first non-compensation

RIEC-Core G0-G6 qualification is evaluated for the frozen action and claim. FAIL or action-relevant NOT_EVALUABLE blocks T2/T3 regardless of confirmation performance. The Agent layer cannot repair a Core gate after C access.

### RA-020 — Numerical confirmation cannot repair the wrong question

A significant C result for the wrong estimand, unit, population, deployment world, evidence identity or claim world remains ineligible. It may be retained as diagnostic evidence only.

### RA-021 — Numerical authority is independently required

Passing all Core gates does not by itself establish that the selected numerical claim replicates. T3 additionally requires valid C evidence satisfying the frozen directional, uncertainty and minimum-effect rule.

### RA-022 — Final effect comes from confirmation

The T3 point estimate and interval are computed from C under the frozen estimator. The selected D estimate is reported separately as development evidence. If C was used to choose among candidates, a valid simultaneous/selective procedure or new C is required.

### RA-023 — Practical and statistical threshold separation

Each T3 directional claim freezes a minimum effect of scientific interest `delta`. Confirmation requires the simultaneous confidence interval to exclude the null and satisfy the registered relation to `delta`; a small p-value alone does not justify a practically meaningful claim. Null/equivalence claims require a registered equivalence margin and valid interval rule.

## F. Decisions, missingness and reporting

### RA-024 — Bounded action set

The Agent layer may return `CONFIRM`, `QUALIFY`, `DOWNGRADE`, `ABSTAIN`, `DIAGNOSTIC_ONLY`, or `PROTOCOL_INVALID`. It cannot silently substitute a different claim. The final language is bounded by the lower of Core and Agent authority.

### RA-025 — Intention-to-run preservation

All frozen episodes and agent assignments remain in the ledger. Timeouts, malformed submissions, refusals and provider failures are terminal outcomes, not deletable nuisance records. Completion thresholds and missingness sensitivity are frozen before execution.

### RA-026 — No favorable reruns

A failed episode may be retried only under the frozen transient-error policy with identical configuration and before any outcome inspection. Otherwise it remains INCOMPLETE. Replacement models, seeds or prompts require a new arm.

### RA-027 — Safety and coverage are co-reported

Unsupported claims, false blocking, true-claim coverage, abstention, downgrade, regret, protected-evidence consumption, latency and operational completion are reported separately. A composite utility is secondary and requires preregistered costs.

### RA-028 — Null and adverse-result permanence

Negative, null, FAIL, NOT_EVALUABLE, contaminated, incomplete and non-replicating records are immutable scientific outputs. They cannot be removed from denominators except under a frozen endpoint-specific missingness rule.

### RA-029 — Version boundary

Any post-freeze change to thresholds, claim families, evidence partitions, feedback payloads, controller, agent roster, prompts affecting scientific behavior, or adjudication logic creates a new protocol version. RIEC-Agent changes never rewrite RIEC-Core v1.0.

