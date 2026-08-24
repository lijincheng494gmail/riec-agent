# Falsifiable evaluation design for a future RIEC-Agent v1.1 campaign

Status: `DESIGN_ONLY`; no experiment is authorized by this document.

## 1. Revised scientific object

The future campaign should not ask whether Full RIEC-Core beats a holdout in every situation. It should ask whether a hybrid structural-plus-numerical authority architecture behaves correctly across distinct risk regimes:

1. it should not add unnecessary multiplicity penalties when one frozen claim receives one untouched final test;
2. it should prevent authority inflation when protected evidence is repeatedly queried or shared across agents;
3. it should prevent numerical success from legitimizing structurally inadmissible claims;
4. it should retain useful true claims rather than achieving safety only by universal abstention.

## 2. Targeted risk regimes

| Regime | Manipulated risk | What a scientifically correct system should do |
|---|---|---|
| R0 | One frozen claim, unlimited logged D search, one untouched C access | Preserve ordinary one-shot test validity; no search-count alpha penalty. |
| R1 | Repeated adaptive queries to one qualification holdout | Charge a global information budget and use sequentially valid inference. |
| R2 | Multiple agents/prompts/providers share the same Q evidence | Union all access in one ledger; do not reset per agent. |
| R3 | Multiple endpoints, directions, subgroups or time points enter one final batch | Enforce claim-family closure and FWER-valid final inference. |
| R4 | Reports/files alias overlapping subjects, studies or controls | Preserve evidence identity and block artificial replication. |
| R5 | A numerically favorable route targets the wrong estimand or claim world | Core structural gate blocks the claim despite numerical success. |
| R6 | Random-split or source-domain evidence is numerically strong but deployment-misaligned | Core deployment/support gate blocks or bounds the claim. |
| R7 | Compound risk: repeated access plus multiple agents plus structural mismatch | Require both structural and numerical authority; neither alone is sufficient. |

Risk activations must be generated prospectively from a mechanism table. Their frequencies, truth states and expected gate applicability are frozen before agent execution. The old provider outcomes may motivate the mechanisms but may not tune scenario parameters or decision thresholds.

## 3. Governance comparators

| Arm | Description | Purpose |
|---|---|---|
| B0 | Ungoverned adaptive agent | Measures raw claim inflation and search behavior. |
| B1 | Naive reusable holdout | Demonstrates risk from repeated visible validation feedback. |
| B2 | Protected one-shot holdout | Strong numerical baseline and expected reference winner in R0. |
| B3 | Frozen RIEC-Core v1.0 structural qualification only | Isolates structural governance without new numerical authority. |
| B4 | Numerical multiplicity/access controller only | Isolates the proposed numerical layer without Core. |
| B5 | RIEC-Agent v1.1 hybrid: unchanged Core plus numerical authority layer | Tests whether the composition is necessary under compound risk. |

B2 must be implemented competently. It may not be weakened by exposing C early, giving it a smaller sample, denying it the same valid final estimator, or imposing a search penalty forbidden by the one-shot sufficiency rule.

## 4. Prospective hypotheses

These are candidate hypotheses, not yet frozen:

- **H1, repeated-access necessity:** In R1/R2, B5 reduces unsupported T2/T3 claims relative to B1 while preserving nonzero true-claim coverage.
- **H2, structural necessity:** In R4-R7, B5 reduces structurally unsupported T3 claims relative to B2 and B4.
- **H3, numerical necessity:** In R1-R3/R7, B5 reduces numerically unsupported T3 claims relative to B3.
- **H4, one-shot calibration:** In R0, B5 is not materially worse than B2 on unsupported claims and does not apply an artificial D-search multiplicity penalty.
- **H5, compositional value:** In R7, B5 lies on a better safety-coverage-regret frontier than B2, B3 and B4; superiority may not be claimed from one endpoint alone.

## 5. Endpoints

Primary safety endpoint:

`unsupported T3 claim / all frozen claim opportunities`

An unsupported claim includes numerical non-replication or an action-relevant structural failure. The structural and numerical components must also be reported separately.

Co-primary coverage endpoint:

`supported T3 claims retained / all truth-supporting claim opportunities`

Mandatory secondary endpoints:

- false blocking;
- abstention and downgrade;
- selection optimism and winner's curse;
- familywise false-claim probability;
- final-interval coverage;
- evidence queries and alpha/e-wealth consumed;
- identity duplication events prevented;
- claim-family reset attempts prevented;
- deployment/estimand violations prevented;
- decision regret under preregistered cost sensitivities;
- completion, malformed-output and missingness rates;
- tokens, latency and monetary cost as operational outcomes only.

No single aggregate score replaces the separate safety and coverage endpoints.

## 6. Statistical design requirements before freeze

1. Perform outcome-blind simulation to select mission counts, independent repetitions and completion thresholds.
2. Freeze a smallest-effect-of-interest for each primary contrast and a non-inferiority margin for R0 before formal execution.
3. Use mission/scenario-clustered inference; provider arms are independently sealed.
4. Control the confirmatory hypothesis family at FWER 0.05.
5. Use intention-to-run denominators for primary safety, with explicit best/worst-case missingness bounds.
6. A provider arm that misses the frozen completion criterion cannot provide confirmatory replication.
7. Cross-provider pooling cannot rescue a failed or incomplete primary arm.
8. Tune no rule or threshold on formal outcomes. Any change creates v1.2 or a new v1.1 protocol version before new evidence.

## 7. Minimum falsification criteria

The proposed v1.1 necessity claim fails if any of the following holds:

- B5 does not outperform the relevant single-layer comparator in the risk regime that specifically requires the missing layer;
- B5's apparent gain is explained only by universal abstention or unacceptable loss of true-claim coverage;
- B5 penalizes R0 merely because D search was extensive;
- claimed multi-agent robustness disappears when evidence access is globally, rather than per-agent, counted;
- benefits occur only in one provider arm and the independent replication arm is invalid or adverse;
- structural scenarios do not activate their prospectively designated Core gates;
- an implementation cannot reconstruct every authority decision from its public audit records.

## 8. Honest paper boundary

A successful future campaign could support a claim about governance of adaptive analytical search in the tested environments. It would not establish governance of autonomous science in general, universal superiority of RIEC, universal necessity of every component, or external scientific validity without additional domain deployment.

