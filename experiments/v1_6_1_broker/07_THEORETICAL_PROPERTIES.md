
# Broker properties and assumptions

## Global non-compensation

An unqualified route cannot support a formal claim regardless of score or p-value.

## Identity invariance

Aliases mapped to the same authority key return the cached decision and cannot create a new authority allocation.

## Persistent budget conservation

The broker state persists across agents, claims, and rounds. In a world with `M` reachable authority keys, each key receives at most `0.050/M`; therefore the sum of allocations is at most `0.050`.

## FWER proposition

If every null authority p-value is super-uniform conditional on the pre-query history, authority identity mapping is correct, and a formal claim requires `p <= alpha_u`, then by the union bound the probability of any unsupported null claim is at most `sum(alpha_u) <= 0.050`. Dependence among authorities does not invalidate this bound. The property does not cover invalid p-values, incorrect identity maps, leakage, outcome-dependent remapping, or claims outside the frozen family.

## Claim monotonicity

Removing structural qualification or downgrading authority cannot strengthen the maximum permitted claim.
