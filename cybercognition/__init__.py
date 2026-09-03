"""
Cybercognition: Minimal falsifiable kernel for cognitive-computer architecture.

Separates NeuralState, CybercognitiveState, and DeterministicState with
structural invariants preventing premature conversion of probabilistic cognition
into deterministic commitment.
"""

__version__ = "0.1.0"

from cybercognition.states import (
    NeuralState,
    CybercognitiveState,
    DeterministicState,
)
from cybercognition.epistemics import (
    EpistemicStatus,
    Hypothesis,
    Binding,
    Evidence,
    Provenance,
    OpenWorkItem,
    Discrepancy,
    VerificationReceipt,
)
from cybercognition.gates import CommitGate
from cybercognition.transitions import (
    externalize,
    refine,
    verify,
    commit,
)
from cybercognition.audit import AuditEvent, AuditLog

__all__ = [
    "NeuralState",
    "CybercognitiveState",
    "DeterministicState",
    "EpistemicStatus",
    "Hypothesis",
    "Binding",
    "Evidence",
    "Provenance",
    "OpenWorkItem",
    "Discrepancy",
    "VerificationReceipt",
    "CommitGate",
    "externalize",
    "refine",
    "verify",
    "commit",
    "AuditEvent",
    "AuditLog",
]
