# RIEC-Agent v1.1 targeted risk-activation microbenchmark

Status before formal execution: `DEVELOPMENT_ONLY_NOT_PREFROZEN`

## Bound inputs

- Rule-design ledger SHA-256: `7de7c487082a4d17d392999c6cf31e55129994b84af9c74b45c29bdc14e3d9a3`
- Executable-validation ledger SHA-256: `b5930b02f512bf1577b6ea47051b71c520bf49626f01cdb534a9814590aed694`
- Core: unchanged `RIEC-Core v1.0`.

## Purpose

This deterministic microbenchmark asks whether each prospectively defined R0-R7 risk pattern activates its designated Core gate and/or RIEC-Agent rule, produces the expected maximum claim-authority tier, and leaves matched no-risk controls unblocked.

It also performs mutation testing. Deliberately defective adjudicators ignore individual gates or Agent rules. A benchmark that cannot distinguish the correct implementation from these mutants fails.

## Boundaries

- No model or provider calls.
- No stochastic scientific outcome generation.
- No old provider private truth or Neuro access.
- No Core modification.
- Passing establishes risk-activation coverage only, not empirical effectiveness or prefreeze readiness.

