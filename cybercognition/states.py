"""
Core state types for the three distinct regimes.

Invariant I1: NeuralState != CybercognitiveState != DeterministicState
Invariant I9: State objects are immutable.
"""

from dataclasses import dataclass, field
from typing import Any, FrozenSet, Optional
from uuid import uuid4


@dataclass(frozen=True)
class NeuralState:
    """
    Represents output originating from probabilistic/neural cognition.

    - May contain candidates, scores, observations, or opaque model-derived material.
    - Is NOT verified truth.
    - Has NO authority to create DeterministicState.
    - Contains raw probabilistic output without epistemic commitments.

    Invariant I3: NeuralState may only produce a CybercognitiveState candidate
    through an explicit externalization transition.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    content: Any = field(default=None)
    source: Optional[str] = field(default=None)  # e.g., "model_v1", "experiment_id"
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"NeuralState(id={self.id}, source={self.source})"


@dataclass(frozen=True)
class CybercognitiveState:
    """
    A first-class explicit intermediate cognitive regime.

    - May contain hypotheses, bindings, evidence, provenance, open work, discrepancies,
      epistemic status.
    - Content may be explicit while still unresolved, provisional, conflicting, or incomplete.
    - Exists specifically to prevent premature conversion of probabilistic cognition
      into deterministic state.

    Invariant I4: May contain unresolved/open/provisional states without forcing
    them into true/false or committed/uncommitted prematurely.

    Invariant I9: Immutable. Transitions produce new state objects.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    hypotheses: FrozenSet[str] = field(default_factory=frozenset)
    bindings: FrozenSet[tuple] = field(default_factory=frozenset)  # (key, value) pairs
    evidence: FrozenSet[str] = field(default_factory=frozenset)
    provenance: Optional[str] = field(default=None)  # chain of origin
    open_work: FrozenSet[str] = field(default_factory=frozenset)
    discrepancies: FrozenSet[str] = field(default_factory=frozenset)
    epistemic_status: dict = field(default_factory=dict)  # hypothesis_id -> EpistemicStatus
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"CybercognitiveState(id={self.id}, "
            f"hypotheses={len(self.hypotheses)}, "
            f"verified={sum(1 for s in self.epistemic_status.values() if s == 'VERIFIED')})"
        )


@dataclass(frozen=True)
class DeterministicState:
    """
    Contains only explicitly committed deterministic state.

    - Transitions into this regime must be gated.
    - No probabilistic output may directly instantiate or mutate DeterministicState.
    - Represents the committed, auditable ground truth for this architecture.

    Invariant I5: CybercognitiveState -> DeterministicState requires an explicit
    successful gate object.

    Invariant I9: Immutable. Each commitment creates a new state object.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    committed_facts: FrozenSet[tuple] = field(default_factory=frozenset)  # (key, value) pairs
    provenance: str = field(default="")  # must include gate reference
    source_cyber_id: str = field(default="")  # traceback to originating CybercognitiveState
    verification_chain: FrozenSet[str] = field(default_factory=frozenset)  # audit trail
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"DeterministicState(id={self.id}, "
            f"facts={len(self.committed_facts)}, "
            f"source_cyber={self.source_cyber_id})"
        )
