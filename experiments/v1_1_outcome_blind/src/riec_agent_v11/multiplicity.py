"""Small auditable familywise-error controllers used by the validation model."""

from __future__ import annotations


def _validate(p_values: list[float], alpha: float) -> None:
    if not p_values:
        raise ValueError("at least one p-value is required")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    if any((p < 0 or p > 1) for p in p_values):
        raise ValueError("p-values must be in [0,1]")


def bonferroni_rejections(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    _validate(p_values, alpha)
    threshold = alpha / len(p_values)
    return [p <= threshold for p in p_values]


def holm_rejections(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    _validate(p_values, alpha)
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    rejected = [False] * len(p_values)
    for rank, (index, p_value) in enumerate(indexed):
        threshold = alpha / (len(p_values) - rank)
        if p_value > threshold:
            break
        rejected[index] = True
    return rejected


def global_query_threshold(total_registered_queries: int, alpha: float = 0.05) -> float:
    if total_registered_queries < 1:
        raise ValueError("total_registered_queries must be positive")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    return alpha / total_registered_queries

