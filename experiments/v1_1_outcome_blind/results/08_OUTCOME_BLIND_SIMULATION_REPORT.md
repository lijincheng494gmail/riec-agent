# Outcome-blind simulation report

Status: `PASS`

This deterministic Monte Carlo run used only synthetic random variables generated from the frozen protocol. It did not use prior provider outcomes, private campaign truth or Neuro artifacts.

## One-shot sufficiency

Across development search budgets [1, 10, 100, 1000], one untouched final test had false-claim rates [0.0507, 0.0514, 0.0485, 0.0491]. The hybrid and protected one-shot baseline used the same frozen decision and were exactly equal at every budget. Development winner rates increased to [0.0513, 0.3996, 0.9943, 1.0], demonstrating selection pressure without inflating the independent final test.

## Reusable holdout

For query counts [1, 5, 20, 100], naive repeated testing produced false-claim rates [0.0498, 0.2271, 0.6424, 0.9942]. Global query accounting produced [0.0498, 0.0492, 0.0504, 0.0499].

## Structural mismatch

When 30% of otherwise numerically favorable opportunities were structurally inadmissible, numerical-only validation produced an unsupported-confirmation rate of 0.2387; the hybrid produced 0.0000. Coverage among structurally valid opportunities was identical at 0.8041.

## Frozen acceptance checks

- `AC-001` `PASS` — One-shot false-claim rate remains controlled across development budgets: observed=0.05138; max <= 0.06
- `AC-002` `PASS` — One-shot rate does not drift with development search budget: observed=0.0028600000000000014; range <= 0.015
- `AC-003` `PASS` — Hybrid exactly preserves the competent one-shot baseline in R0: observed=1; equal false claims and true claims at every budget
- `AC-004` `PASS` — Naive repeated holdout access exhibits large false-claim inflation: observed=0.9444; q100-q1 >= 0.8
- `AC-005` `PASS` — Global repeated-access and final-family controllers preserve null error: observed=0.0509; max <= 0.06
- `AC-006` `PASS` — Numerical-only validation admits structurally unsupported claims: observed=0.23874; >= 0.15
- `AC-007` `PASS` — Hybrid blocks structurally invalid claims: observed=0.0; == 0.0
- `AC-008` `PASS` — Structural gate does not reduce coverage for structurally valid claims in this oracle test: observed=0.0; <= 0.0

## Interpretation boundary

`SIMULATION_VALIDATION=PASS` means only that the reference rules behaved as specified under the frozen synthetic generators. It does not establish empirical effectiveness, provider robustness, real scientific validity or publication-level RIEC-Agent superiority.
