# RIEC-Agent v1.1 evidence-authority model

## 1. Objects

The governance object is not an isolated model answer. It is a tuple:

`(scientific claim, claim family, search lineage, evidence identities, access history, structural gate snapshot, numerical controller, action)`

A formally eligible claim must be reconstructible from this tuple without access to hidden model reasoning. Chain-of-thought is neither required nor treated as scientific evidence. Executed analysis calls, observations returned to the agent, route changes, claim changes and evidence access are required.

## 2. Claim-authority lattice

Authority is ordinal and non-compensatory:

| Tier | Label | Maximum permitted statement |
|---|---|---|
| T0 | DIAGNOSTIC | A computation, failure, discrepancy or audit observation occurred. |
| T1 | EXPLORATORY | Development evidence suggests a pattern that requires independent qualification. |
| T2 | QUALIFIED | A frozen candidate passed an independent, multiplicity-valid qualification procedure; it is not yet a final confirmatory result. |
| T3 | CONFIRMATORY | A predeclared claim and route passed Core qualification and a fresh, familywise-valid final confirmation procedure. |
| T4 | REPLICATED | A T3 claim passed a separately frozen replication on a new evidence identity or declared external deployment world. |

For claim `c`, final authority is the meet of independent dimensions:

`A(c) = Structural(c) ∧ Lineage(c) ∧ Identity(c) ∧ Access(c) ∧ Multiplicity(c) ∧ Confirmation(c)`

No high value in one dimension compensates for a lower value in another. A Core hard-gate failure caps authority at T0 regardless of predictive performance or p-value.

## 3. Evidence pools

### D — Development/search evidence

- May be queried adaptively within a frozen operational ceiling.
- May guide hypotheses, routes, models, preprocessing and stopping.
- Carries at most T1 authority.
- All broker-visible evaluations and feedback must enter the global lineage ledger.

### Q — Qualification evidence

- Independent of D and accessed only through a registered broker.
- May support candidate filtering or T2 claims.
- Repeated/adaptive access requires a valid sequential controller and a global access budget.
- Exact Q outputs revealed to an agent permanently disqualify Q from later serving as C for the same claim family.

### C — Final confirmation evidence

- Independent of D and Q for the claim family.
- Remains sealed until route, claim family, direction, estimand, population, minimum effect of interest, decision rule and multiplicity allocation are frozen.
- Is released once, in a batch, after all final claims are submitted.
- Supplies the effect estimate and uncertainty used for T3 language.

### R — Replication evidence

- New evidence identity or externally declared deployment world.
- Governed by a new freeze and cannot be created by repartitioning C after seeing it.

## 4. One-shot sufficiency

If one claim is frozen before one access to an untouched independent C pool, and the test/interval is valid, arbitrary D-stage search does not by itself require Bonferroni correction over every development route. The selection is evaluated by C, not by the maximum D result.

Consequences:

1. Search count remains mandatory audit information but is not automatically an alpha denominator.
2. Multiplicity adjustment applies to the family of claims tested on C and to repeated/adaptive access to protected evidence.
3. If C influences route or claim selection, it is no longer a one-shot confirmation set.

## 5. Claim-family closure

A claim family contains all executed or proposed variants that answer the same substantive proposition while varying direction, endpoint, subgroup, time point, metric, model, estimand label, population slice or wording. Claim-family identity is frozen before C access.

Rephrasing, changing the sign, narrowing to a discovered subgroup, switching endpoints or replacing a null claim with a heterogeneous claim after feedback does not create a new family or reset evidence spending.

## 6. Global union across agents

For agents `a1...ak` operating on the same scientific claim family and evidence identity:

`Ledger_global = union(Ledger_a1, ..., Ledger_ak)`

All Q/C access debits and all tested final claims are counted globally. A new model, prompt, seed, session or provider does not reset the ledger. Agreement between agents is search consensus, not independent data replication.

## 7. Formal properties required of an implementation

1. **Non-compensation:** numerical strength cannot override structural ineligibility.
2. **Authority monotonicity:** degrading identity, provenance, access state or controller validity cannot increase claim authority.
3. **Identity invariance:** copying, renaming or re-encoding one evidence identity cannot increase independent support.
4. **Agent-union invariance:** splitting one search across more agents cannot increase the total evidence budget.
5. **Access irreversibility:** once protected evidence releases information, it cannot return to an untouched state.
6. **Claim-family closure:** post-feedback wording changes cannot reset multiplicity accounting.
7. **One-shot validity:** unlimited registered D search does not reduce T3 authority when a single claim is frozen and evaluated once on untouched C.
8. **Optional-stopping validity:** T2/T3 claims based on sequential protected-evidence access require an anytime-valid or fully prespecified alpha-spending procedure.
9. **Effect-authority separation:** the development winner may identify a candidate but cannot supply its final confirmatory effect estimate.
10. **Version irreversibility:** changes to rules, thresholds, evidence partitions or claim-family mapping require a new freeze/version.

