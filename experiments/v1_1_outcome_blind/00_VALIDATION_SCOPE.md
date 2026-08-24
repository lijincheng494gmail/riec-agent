# RIEC-Agent v1.1 executable rule validation scope

Status before execution: `DEVELOPMENT_VALIDATION_ONLY`

## Bound design

- Design directory: `<LOCAL_WORKSPACE_ROOT>/RIEC_AGENT_V1_1_RULE_DESIGN/design_20260815T220449Z`
- Design checksum-ledger SHA-256: `7de7c487082a4d17d392999c6cf31e55129994b84af9c74b45c29bdc14e3d9a3`
- Inherited Core: `RIEC-Core v1.0`, unchanged.

## Authorized work

1. Implement the draft authority projection, evidence state machine, global ledger and multiplicity controllers as a standalone validation model.
2. Execute deterministic property/model-check tests.
3. Execute synthetic outcome-blind Monte Carlo simulations defined before result generation.
4. Record all failures, including a conclusion that the rules are inconsistent or do not control the intended error process.

## Prohibited work

- No LLM/API/provider calls.
- No cloud, VM, SSH or internet.
- No access to old Neuro-A/B outcomes or lockboxes.
- No access to the previous provider campaign's private truth.
- No changes to RIEC-Core v1.0.
- No empirical scientific claim from simulation alone.
- No promotion to prefreeze readiness merely because software tests pass.

## Validation questions

1. Are authority decisions non-compensatory and monotone under degradation of evidence conditions?
2. Is protected-evidence access irreversible?
3. Does splitting one search across agents fail to create new evidence or reset query spending?
4. Does one untouched final test maintain its nominal false-positive rate as development search grows?
5. Does naive repeated holdout access inflate false claims, while global multiplicity accounting controls them?
6. Does the hybrid block numerically significant but structurally inadmissible claims without degrading the correctly implemented one-shot control?

