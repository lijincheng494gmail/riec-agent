"""Executable reference model for RIEC-Agent v1.1 design validation."""

from .authority import AuthorityContext, AuthorityTier, CoreStatus, EvidenceState, project_authority
from .ledger import GlobalEvidenceLedger, LedgerEvent
from .multiplicity import bonferroni_rejections, holm_rejections
from .state_machine import AccessEvent, InvalidTransition, ProtectedEvidenceState, transition

__all__ = [
    "AccessEvent",
    "AuthorityContext",
    "AuthorityTier",
    "CoreStatus",
    "EvidenceState",
    "GlobalEvidenceLedger",
    "InvalidTransition",
    "LedgerEvent",
    "ProtectedEvidenceState",
    "bonferroni_rejections",
    "holm_rejections",
    "project_authority",
    "transition",
]

