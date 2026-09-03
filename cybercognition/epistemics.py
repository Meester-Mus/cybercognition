"""
Epistemic types for representing knowledge states within CybercognitiveState.

Invariant I6: A model assertion such as "X is verified" MUST NOT itself produce
verified or deterministic state. Verification is a transition, not an assertion.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import uuid4


class EpistemicStatus(Enum):
    """
    Minimal distinctions for epistemic state.

    POSSIBLE: A hypothesis or claim exists as a candidate, unverified.
    VERIFIED: Explicit verification transition has been applied and recorded,
              but this does NOT imply DeterministicState commitment.

    Invariant: Do NOT collapse CANONICAL/COMMITTED into VERIFIED.
    Deterministic commitment must remain a separate transition.
    """

    POSSIBLE = "POSSIBLE"
    VERIFIED = "VERIFIED"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Hypothesis:
    """
    Represents a candidate claim or belief within CybercognitiveState.

    A hypothesis:
    - Has unique identity
    - May coexist with contradictory hypotheses
    - May be in POSSIBLE or VERIFIED epistemic status
    - Cannot directly become DeterministicState
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = field(default="")
    status: EpistemicStatus = field(default=EpistemicStatus.POSSIBLE)
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"Hypothesis(id={self.id}, status={self.status}, content='{self.content[:50]}')"


@dataclass(frozen=True)
class Binding:
    """
    Represents an association or constraint within CybercognitiveState.

    A binding:
    - Links a key to a value or constraint
    - Exists in provisional state until explicitly committed
    - Does not represent database constraint or truth
    """

    key: str = field(default="")
    value: str = field(default="")
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"Binding({self.key}={self.value})"


@dataclass(frozen=True)
class Evidence:
    """
    Represents data supporting or refuting a hypothesis.

    Evidence:
    - Has source and content
    - Does not itself determine verification
    - Feeds into explicit verification transitions
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    hypothesis_id: str = field(default="")
    content: str = field(default="")
    source: Optional[str] = field(default=None)
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"Evidence(id={self.id}, for={self.hypothesis_id})"


@dataclass(frozen=True)
class Provenance:
    """
    Tracks the origin and history of state transitions.

    Invariant I8: State transitions must be auditable.
    """

    origin: str = field(default="")  # source regime or external origin
    chain: tuple = field(default_factory=tuple)  # list of transition IDs
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"Provenance(origin={self.origin}, chain_len={len(self.chain)})"


@dataclass(frozen=True)
class OpenWorkItem:
    """
    Represents explicit unresolved work within CybercognitiveState.

    Invariant I4: CybercognitiveState may contain open/provisional states
    without forcing them into true/false or committed/uncommitted prematurely.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = field(default="")
    related_hypotheses: frozenset = field(default_factory=frozenset)
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"OpenWorkItem(id={self.id}, desc='{self.description[:40]}')"


@dataclass(frozen=True)
class Discrepancy:
    """
    Represents conflicting claims within CybercognitiveState.

    Invariant I4: Conflicting hypotheses may coexist without automatic resolution.

    Invariant I6 related: A discrepancy is not resolved by a model claiming
    "this is resolved" — resolution requires explicit transition.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    hypothesis_a_id: str = field(default="")
    hypothesis_b_id: str = field(default="")
    nature: str = field(default="")  # e.g., "contradiction", "mutual_exclusion"
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"Discrepancy(id={self.id}, {self.hypothesis_a_id} vs {self.hypothesis_b_id})"


@dataclass(frozen=True)
class VerificationReceipt:
    """
    Explicit artifact of a verification transition.

    A VerificationReceipt:
    - Is produced by a successful verify() transition
    - Certifies that a hypothesis has undergone explicit verification
    - Does NOT automatically commit the hypothesis to DeterministicState
    - Includes provenance for auditability

    Invariant I6: The receipt itself is not a claim that can be asserted by NeuralState.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    hypothesis_id: str = field(default="")
    verification_method: str = field(default="")  # e.g., "manual_review", "test_suite"
    verified_at: str = field(default="")  # timestamp or event reference
    evidence_ids: frozenset = field(default_factory=frozenset)
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"VerificationReceipt(id={self.id}, verified={self.hypothesis_id})"
