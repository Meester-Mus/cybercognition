"""
Audit trail for tracking state transitions.

Invariant I8: State transitions must be auditable.
"""

from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4
from datetime import datetime


@dataclass(frozen=True)
class AuditEvent:
    """
    Records a single state transition event.

    Invariant I8: Every successful regime crossing produces an AuditEvent
    containing source regime, target regime, transition type, and
    provenance/reference information.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    transition_type: str = field(default="")  # externalize, refine, verify, commit
    source_regime: str = field(default="")  # NeuralState, CybercognitiveState, DeterministicState
    target_regime: str = field(default="")
    source_id: str = field(default="")  # id of source state object
    target_id: str = field(default="")  # id of target state object
    provenance: str = field(default="")  # chain reference or gate id
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"AuditEvent(id={self.id}, "
            f"{self.source_regime} -> {self.target_regime}, "
            f"type={self.transition_type})"
        )


@dataclass
class AuditLog:
    """
    Accumulates audit events for a session or component.
    """

    events: list = field(default_factory=list)

    def record(self, event: AuditEvent) -> None:
        """Record a single audit event."""
        self.events.append(event)

    def get_transitions(self, source_regime: Optional[str] = None) -> list:
        """Get all events, optionally filtered by source regime."""
        if source_regime is None:
            return self.events
        return [e for e in self.events if e.source_regime == source_regime]

    def __str__(self) -> str:
        return f"AuditLog(events={len(self.events)})"
