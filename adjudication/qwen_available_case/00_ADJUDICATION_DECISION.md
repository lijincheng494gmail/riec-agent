# Qwen available-case adjudication decision

The original v1.6.1 confirmatory run remains permanently recorded as `FAIL_CLOSED_BEFORE_C` under its frozen all-sessions-complete gate.

Following explicit user adjudication on 2026-08-16, the eight zero-token, zero-response `TRANSPORT_FAILURE` records are treated as operational missingness. They are retained and are not converted into model answers, behavioral failures, or successful sessions. No session is rerun. The remaining 1,912 accepted sessions are scored as an available-case analysis.

Because this decision was made after the technical failure, the resulting analysis is labelled `POST_FAILURE_USER_AUTHORIZED_AVAILABLE_CASE`, not a pristine prospective confirmation. A complete-world sensitivity analysis excludes every world touched by a missing session. An extreme H1 sensitivity bound additionally assigns all six affected worlds in the direction least favorable to R4.

Original source run: `<LOCAL_WORKSPACE_ROOT>/RIEC_AGENT_V1_6_1_QWEN_FINAL_CONFIRMATION/run_20260816T122353Z`
Original source run modified: `NO`
Accepted sessions: `1912`
Transport-missing sessions: `8`
Affected worlds: `6`
