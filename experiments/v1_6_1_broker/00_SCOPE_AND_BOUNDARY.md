
# RIEC-Agent v1.6.1 broker calibration and final scientific prefreeze

This local-only stage preserves and checksum-verifies the completed DeepSeek and GPT evidence packages, calibrates the persistent broker without LLM calls, validates the locked parameter on a disjoint seed family, activates the claimed failure modes, and freezes the next provider experiment. It does not rerun, overwrite, or reinterpret v1.4/v1.5 outcomes. It does not call Qwen, DeepSeek, GPT, cloud, VM, or SSH. RIEC-Core v1.0 is not modified.

The selected broker family budget is `0.050`. This is a prospective v1.6.1 parameter, not a retroactive repair of v1.5 or conversion of failed v1.6 into PASS. v1.6.1 uses entirely new calibration, validation, and targeted seeds. Its only design correction is replacing the over-constrained N5 per-regime minimum effect size with a directional N5 check while retaining the aggregate B3-minus-R4 requirement of at least 0.08.
