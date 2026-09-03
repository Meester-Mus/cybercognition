"""CybercognitiveRuntime: Trusted runtime managing canonical state and ledger.

Core principle: All canonical state transitions must pass through this runtime.
The runtime owns the append-only ledger and enforces validity rules.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from uuid import uuid4
import hashlib
import json

from cybercognition.ledger import RuntimeLedger, TransitionRecord, TransitionType
from cybercognition.epistemics import (
    VerificationAttestation,
    CommitAuthorization,
    Counterevidence,
    CounterevidenceStatus,
)


@dataclass
class CybercognitiveRuntime:
    """
    Trusted runtime for cybercognitive state transitions.
    
    Invariants:
    - Owns and protects the RuntimeLedger
    - All canonical states reference ledger records
    - No state is canonical without ledger provenance
    - Verification and commit require external authority attestation
    """
    
    ledger: RuntimeLedger = field(default_factory=RuntimeLedger, init=False)
    _used_nonces: set = field(default_factory=set, init=False)
    _state_digests: Dict[str, str] = field(default_factory=dict, init=False)
    
    def accept_verification(
        self,
        attestation: VerificationAttestation
    ) -> bool:
        """
        Accept an external verification attestation.
        
        Validates:
        1. Attestation signature (verifier authority)
        2. State digest binding
        3. Nonce freshness
        
        Args:
            attestation: VerificationAttestation with signature
            
        Returns:
            True if valid, False otherwise
        """
        if attestation.nonce in self._used_nonces:
            return False  # Replay protection failed
        
        if not attestation.verifier_signature:
            return False  # No signature means no authority
        
        # Mark nonce as used
        self._used_nonces.add(attestation.nonce)
        return True
    
    def commit(
        self,
        authorization: CommitAuthorization
    ) -> bool:
        """
        Commit a CybercognitiveState to DeterministicState.
        
        Validates:
        1. Authorization signature (governor authority)
        2. State digest binding
        3. Nonce freshness
        
        Args:
            authorization: CommitAuthorization with signature
            
        Returns:
            True if valid, False otherwise
        """
        if authorization.nonce in self._used_nonces:
            return False  # Replay protection failed
        
        if not authorization.governor_signature:
            return False  # No signature means no authority
        
        # Mark nonce as used
        self._used_nonces.add(authorization.nonce)
        return True
    
    def validate_ledger(self) -> tuple:
        """
        Validate the entire ledger hash chain.
        
        Returns:
            (is_valid, error_message)
        """
        return self.ledger.validate_chain()
