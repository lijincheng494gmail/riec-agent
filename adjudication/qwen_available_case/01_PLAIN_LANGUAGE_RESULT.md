# Qwen v1.6.1 available-case result

## Bottom line

The 1,912 returned sessions produce an available-case joint result of **PASS**. The complete-world sensitivity result, which removes all six worlds touched by a transport failure, is **PASS**. Under the deliberately extreme assumption that every affected world would have favored B3 over R4, the joint result is **PASS**.

This does not rewrite the original run: its preregistered all-complete confirmation status remains `FAIL_CLOSED_BEFORE_C`. The result below has `POST_FAILURE_USER_AUTHORIZED_AVAILABLE_CASE` authority.

## Main numerical result

- B3 multi-claim null risk: **22.5% (18/80)**
- R4 persistent-broker multi-claim null risk: **2.5% (2/80)**
- B1 alias-signal coverage: **0.0% (0/24)**
- R4 persistent-broker alias-signal coverage: **37.5% (9/24)**
- H1 paired evidence: favorable `16`, adverse `0`, one-sided p=`1.5258789e-05`
- H2 paired evidence: favorable `9`, adverse `0`, one-sided p=`0.001953125`
- Holm family pass: **TRUE**
- R4 alpha-ledger invariant: **TRUE**

## Missingness sensitivity

- Planned sessions: `1920`
- Accepted sessions: `1912`
- Zero-token transport-missing sessions: `8`
- Completion rate: `99.583%`
- Worlds touched by transport failure: `6`; all were NULL worlds, so H2 signal coverage is unaffected.
- Complete-world H1: favorable `15`, adverse `0`, p=`3.0517578e-05`
- Complete-world H2: favorable `9`, adverse `0`, p=`0.001953125`
- Extreme adverse H1 bound: favorable `15`, adverse `6`, p=`0.039176941`; Holm family pass **TRUE**

## Interpretation boundary

These results test whether a persistent evidence broker controls unsupported claims while preserving discovery in this frozen synthetic multi-agent evidence market. They do not prove universal superiority over every correction method, universal Qwen behavior, or real-world scientific benefit.
