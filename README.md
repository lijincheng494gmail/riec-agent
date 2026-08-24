# RIEC-Agent

Executable research package for a local-to-global failure of evidential control under adaptive multi-agent search.

Public preprint: [RIEC-Agent: Local Evidential Compliance Does Not Compose Under Adaptive Multi-Agent Search](https://doi.org/10.2139/ssrn.7298738).

The central question is compositional: **if every agent satisfies its own local evaluation rule, does the population necessarily preserve system-level evidential validity?** In the tested synthetic evidence market, the answer was no. Agents could reuse finite shared evidence across claims, aliases and rounds while remaining locally compliant, causing multiplicity to accumulate outside each local ledger.

## Main result

Outcome-blind simulation first established the sufficiency boundary. A genuinely untouched one-shot test remained calibrated after extensive development search, while repeated adaptive access to the same holdout increased false-claim probability from 0.0498 after one query to 0.9942 after 100 queries.

The frozen v1.6.1 benchmark then compared:

- **B1 raw global Bonferroni** — charges every query;
- **B2 online global spending** — globally allocates decreasing query weights;
- **B3 locally reset identity-aware Bonferroni** — deduplicates locally but forgets spending across agents and claims;
- **R4 persistent broker** — maintains an evidence-identity × claim-family ledger across agents and rounds.

Across 36,000 independent validation worlds, R4 controlled null-world family-wise error at 0.0428 versus 0.1293 for B3, while retaining 0.7126 difficult-signal coverage in the alias-activation regime where B1 recovered none.

The supporting Qwen run returned 1,912 of 1,920 planned sessions. Available-case ordering agreed with the simulation: unsupported null-world claims were 18/80 for B3 and 2/80 for R4; difficult-signal recovery was 0/24 for B1 and 9/24 for R4. The eight zero-token transport failures are retained. The original all-complete confirmation remains `FAIL_CLOSED_BEFORE_C`; the available-case adjudication does not rewrite it.

## Mechanism in the alias-activation regime

B1 and R4 used the same per-test threshold, 0.00625. B1 did not lose signal because its threshold was stricter. Identity-blind charging consumed both available query/action slots on an evidence object and its alias, so the later target evidence was never reached. R4 recognized the alias as the same evidence identity and preserved the next slot for the target. This is a resource-allocation difference, not a hidden relaxation of error control.

## Repository map

- `protocols/v1_1_design/` — evidence-authority model, rulebook and design decisions;
- `experiments/v1_1_outcome_blind/` — one-shot/repeated-access property tests and curves;
- `experiments/v1_1_microbench/` — targeted risk activation and mutation tests;
- `experiments/v1_6_1_broker/` — frozen broker protocol, simulator and independent validation;
- `provider/qwen_v1_6_1/` — compact provider protocol, prompts and failure-preserving audit;
- `adjudication/qwen_available_case/` — authorized post-failure available-case analysis;
- `figures/` — four final manuscript figures;
- `docs/` — claim, failure and projection boundaries.

## Offline reproduction

All primary simulations use the Python standard library.

```bash
python experiments/v1_1_outcome_blind/run_property_tests.py
python experiments/v1_1_outcome_blind/simulation/run_outcome_blind_simulation.py
python experiments/v1_1_microbench/run_unit_tests.py
python experiments/v1_1_microbench/run_targeted_microbench.py
python -m unittest discover -s experiments/v1_6_1_broker/tests
```

Provider API execution is not required for these offline checks and is intentionally not the default quickstart.

## Boundary

The results establish a failure mode and a safety-discovery trade-off within the tested synthetic multi-agent evidence market. They do not prove universal broker superiority, universal provider behavior, all-domain AI4Science validity or real-world scientific benefit. See [`docs/CLAIM_BOUNDARY.md`](docs/CLAIM_BOUNDARY.md).

No explicit open-source license was present in the verified source package; see [`LICENSE_NOTICE.md`](LICENSE_NOTICE.md).
