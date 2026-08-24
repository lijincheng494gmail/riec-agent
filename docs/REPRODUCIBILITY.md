# Reproducibility guide

## Primary offline evidence

The property tests, risk-activation microbenchmark and v1.6.1 simulator require no model API and use deterministic seeds recorded in their frozen protocols.

```bash
python experiments/v1_1_outcome_blind/run_property_tests.py
python experiments/v1_1_outcome_blind/simulation/run_outcome_blind_simulation.py
python experiments/v1_1_microbench/run_unit_tests.py
python experiments/v1_1_microbench/run_targeted_microbench.py
python -m unittest discover -s experiments/v1_6_1_broker/tests
```

Expected headline checks:

- one-shot false-claim probability remains near 0.05;
- repeated-access false-claim probability reaches 0.9942 at 100 queries;
- v1.6.1 independent validation contains 36,000 worlds;
- R4 null FWER is 0.0428333 and B3 null FWER is 0.1292778;
- R4 alias-regime signal coverage is 0.7126.

## Provider evidence

The compact provider directory retains the frozen prompt/schema, protocol code, audit, cost ledger and transport diagnostic. Raw response dumps and thousands of duplicated session files are omitted from this lightweight GitHub projection. Fresh provider execution would require separate authorization, credentials, network access and cost; it is neither necessary nor implied by the offline reproduction commands.

The available-case adjudication is retained with its manifest and source-seal checks. It should be read together with the original `FINAL_STATUS.txt`.
