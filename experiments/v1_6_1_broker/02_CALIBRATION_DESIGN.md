
# Outcome-blind calibration design

Six null and six signal regimes were fixed in code. Each candidate broker budget in `[0.05, 0.045, 0.04, 0.035, 0.03, 0.025]` was evaluated on 3,000 worlds per regime (36,000 per candidate). The largest candidate satisfying every predeclared guardrail was selected using calibration outcomes only. The validation seed commitment existed before selection, and the parameter-lock file was written before validation was opened.

Selected budget: `0.050`. Selection guardrails: exact one-sided 95% null-FWER upper bound no greater than 0.05; alias-signal coverage at least 0.65; B3-minus-R4 null-risk gap at least 0.08; and no R4 alpha-ledger overspend.
