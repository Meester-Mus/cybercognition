"""
Commit gates: Explicit gating mechanism for CybercognitiveState -> DeterministicState.

Invariant I5: CybercognitiveState -> DeterministicState requires an explicit
successful gate object.

Invariant I7: Unknown or incomplete gate information fails closed.

Invariant I10: The architecture must make illegal transitions structurally
difficult or impossible through its public API.
"""

from dataclasses import dataclass, field
from typing import Optional, Set
from uuid import uuid4


@dataclass(frozen=True)
class CommitGate:
    """
    Explicit gating object required to transition CybercognitiveState -> DeterministicState.

    A CommitGate:
    - Must specify which hypotheses are being committed
    - Must verify that all hypotheses in scope have been verified
    - Must include verification receipt references
    - Must explicitly declare what is NOT being committed
    - Fails closed if information is incomplete or contradictory

    Invariant I7: Incomplete or contradictory gate information causes
    the gate to fail open (reject the transition).
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    
    # Which hypotheses are being committed to deterministic state
    hypotheses_to_commit: frozenset = field(default_factory=frozenset)
    
    # Verification receipts for each hypothesis being committed
    required_receipts: frozenset = field(default_factory=frozenset)
    
    # What we are explicitly NOT committing (for clarity)
    hypotheses_excluded: frozenset = field(default_factory=frozenset)
    
    # Additional validation function name or rule identifier
    validation_rule: Optional[str] = field(default=None)
    
    # Metadata for auditing
    metadata: dict = field(default_factory=dict)

    def is_complete(self) -> bool:
        """
        Check if gate has sufficient information to proceed.

        Returns False (fail closed) if:
        - No hypotheses specified for commitment
        - required_receipts is empty
        - committed and excluded sets overlap
        """
        if not self.hypotheses_to_commit:
            return False
        if not self.required_receipts:
            return False
        
        overlap = self.hypotheses_to_commit & self.hypotheses_excluded
        if overlap:
            return False
        
        return True

    def validate_receipts(self, receipts_by_hyp: dict) -> bool:
        """
        Check if all required receipts are present for hypotheses to commit.

        Args:
            receipts_by_hyp: dict mapping hypothesis_id -> VerificationReceipt or None

        Returns:
            True if all hypotheses to commit have valid receipts, False otherwise.
        """
        for hyp_id in self.hypotheses_to_commit:
            if hyp_id not in receipts_by_hyp:
                # Missing receipt for hypothesis: fail closed
                return False
            if receipts_by_hyp[hyp_id] is None:
                # Null receipt: fail closed
                return False
        return True

    def __str__(self) -> str:
        return (
            f"CommitGate(id={self.id}, "
            f"commit={len(self.hypotheses_to_commit)}, "
            f"receipts={len(self.required_receipts)}, "
            f"complete={self.is_complete()})"
        )
