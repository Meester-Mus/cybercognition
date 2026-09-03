"""
Runtime Ledger: Append-only, hash-chained transition record store.

Core invariant: No deletion, no mutation, no reordering of recorded transitions.
Tamper-evident through hash chaining.

Not claimed as "tamper-proof" - claims only structural immutability
and detectability of modification attempts.
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any, List
from uuid import uuid4
from datetime import datetime
from enum import Enum


class TransitionType(Enum):
    """Types of state transitions recorded in ledger."""
    EXTERNALIZE = "externalize"
    REFINE = "refine"
    VERIFY = "verify"
    COMMIT = "commit"


@dataclass(frozen=True)
class TransitionRecord:
    """
    Immutable record of a single state transition.

    All fields are immutable. Hash chain links to previous record.
    Modification of any field breaks hash chain.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    transition_type: TransitionType = field(default=TransitionType.EXTERNALIZE)
    
    # Source state digest (content-bound identity)
    source_state_digest: str = field(default="")
    
    # Target state digest (content-bound identity)
    target_state_digest: str = field(default="")
    
    # For verification transitions: attestation digest
    attestation_digest: Optional[str] = field(default=None)
    
    # For commit transitions: authorization digest
    authorization_digest: Optional[str] = field(default=None)
    
    # Hash of previous record in chain (immutable chain)
    previous_record_hash: str = field(default="")
    
    # Hash of this record (computed once, immutable)
    this_record_hash: str = field(default_factory=str)
    
    # Additional immutable context (tuples only, no mutable collections)
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def compute_hash(self) -> str:
        """
        Compute canonical hash of this record (excluding the hash itself).
        Deterministic and content-bound.
        """
        # Serialize all fields except this_record_hash
        canonical = json.dumps({
            "id": self.id,
            "timestamp": self.timestamp,
            "transition_type": self.transition_type.value,
            "source_state_digest": self.source_state_digest,
            "target_state_digest": self.target_state_digest,
            "attestation_digest": self.attestation_digest,
            "authorization_digest": self.authorization_digest,
            "previous_record_hash": self.previous_record_hash,
            "metadata": list(self.metadata),
        }, sort_keys=True, separators=(',', ':'))
        
        return hashlib.sha256(canonical.encode()).hexdigest()

    def __post_init__(self):
        """Ensure hash is computed if not provided."""
        if not self.this_record_hash or self.this_record_hash == "":
            object.__setattr__(self, 'this_record_hash', self.compute_hash())


@dataclass
class RuntimeLedger:
    """
    Append-only runtime transition ledger.

    Rules:
    - Records are added only via append()
    - Records are never deleted, mutated, or reordered
    - Hash chain validates integrity
    - Snapshots are immutable tuples
    - No public mutation API
    """

    _records: List[TransitionRecord] = field(default_factory=list, init=False)
    _previous_hash: str = field(default="", init=False)

    def append(self, record: TransitionRecord) -> TransitionRecord:
        """
        Append a record with the ledger's previous hash linked.

        Args:
            record: TransitionRecord to append (should have empty previous_record_hash)

        Returns:
            The record with previous_record_hash set and hash computed.

        Raises:
            ValueError: If record already has non-empty previous_record_hash
        """
        if record.previous_record_hash:
            raise ValueError(
                "Record already has previous_record_hash set; cannot append pre-linked record"
            )

        # Create new record with previous hash linked
        linked_record = TransitionRecord(
            id=record.id,
            timestamp=record.timestamp,
            transition_type=record.transition_type,
            source_state_digest=record.source_state_digest,
            target_state_digest=record.target_state_digest,
            attestation_digest=record.attestation_digest,
            authorization_digest=record.authorization_digest,
            previous_record_hash=self._previous_hash,
            this_record_hash="",  # Will be computed
            metadata=record.metadata,
        )

        # Store in ledger
        self._records.append(linked_record)
        
        # Update previous hash for next record
        self._previous_hash = linked_record.this_record_hash

        return linked_record

    def validate_chain(self) -> Tuple[bool, Optional[str]]:
        """
        Validate entire hash chain integrity.

        Returns:
            (is_valid, error_message)
            If invalid, error_message describes the break.
        """
        prev_hash = ""

        for i, record in enumerate(self._records):
            if record.previous_record_hash != prev_hash:
                return (
                    False,
                    f"Record {i}: previous_record_hash mismatch at index {i}. "
                    f"Expected {prev_hash}, got {record.previous_record_hash}"
                )

            # Recompute hash and verify
            computed_hash = record.compute_hash()
            if record.this_record_hash != computed_hash:
                return (
                    False,
                    f"Record {i}: this_record_hash does not match computed hash. "
                    f"Record may have been tampered with."
                )

            prev_hash = record.this_record_hash

        return (True, None)

    def get_snapshot(self) -> Tuple[TransitionRecord, ...]:
        """
        Return an immutable snapshot of the current ledger.

        Returns:
            Tuple of all records (immutable, read-only view)
        """
        return tuple(self._records)

    def get_record_by_digest(self, digest: str) -> Optional[TransitionRecord]:
        """
        Look up a record by source or target state digest.

        Args:
            digest: State digest to search for

        Returns:
            First matching record or None
        """
        for record in self._records:
            if record.source_state_digest == digest or record.target_state_digest == digest:
                return record
        return None

    def __len__(self) -> int:
        """Return number of records in ledger."""
        return len(self._records)

    def __str__(self) -> str:
        return f"RuntimeLedger(records={len(self._records)}, valid={self.validate_chain()[0]})"
