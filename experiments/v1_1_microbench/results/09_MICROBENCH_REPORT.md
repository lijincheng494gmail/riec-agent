# Targeted risk-activation microbenchmark report

Status: `PASS`

## Exact case behavior

- Cases matching prospectively declared authority/gate/rule/action expectations: `34/34`
- False gate/rule activations in matched controls: `0`
- Required activation items covered: `36/36`
- Risk regimes covered: `8/8`
- Core gates activated by targeted risks: `7/7`
- Required Agent rules activated: `21/21`

## Mutation sensitivity

- Deliberately defective adjudicators killed: `24/24`
- Mutation score: `100.0%`

The mutation suite includes ignored G0-G6 gates, per-agent budget reset, agent-consensus pseudo-replication, invalid sequential testing, unadjusted final multiplicity, repeated/contaminated confirmation access, confirmation-based route selection, ignored practical thresholds or missingness, development-effect promotion, version mutation and an incorrect penalty on extensive development search.

## Boundary

Passing means that the deterministic cases activate the intended mechanisms and detect the declared defective implementations. It does not establish real-agent behavior, calibrated empirical effect size or publication-level component necessity.
