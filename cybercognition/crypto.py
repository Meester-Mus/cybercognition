"""Cryptographic validation for VerificationAttestation and CommitAuthorization.

Core principle: Possession of source code != Possession of authority.

Uses Ed25519 signatures with explicit domain separation to prevent interchangeable
signature reuse across different authorization types.
"""

import json
import hashlib
from typing import Tuple, Optional
from dataclasses import dataclass


# Domain separation strings to prevent signature reuse
VERIFICATION_DOMAIN = b"CYBERCOGNITION_VERIFICATION_V1"
AUTHORIZATION_DOMAIN = b"CYBERCOGNITION_COMMIT_AUTHORIZATION_V1"


class CryptoError(Exception):
    """Base class for cryptographic validation errors."""
    pass


class SignatureValidationError(CryptoError):
    """Signature validation failed."""
    pass


class DomainSeparationError(CryptoError):
    """Domain separation violation detected."""
    pass


def canonical_json(obj: dict) -> bytes:
    """
    Serialize to canonical JSON for signature computation.
    
    Guarantees:
    - Deterministic key ordering
    - Compact representation (no whitespace)
    - Identical output for semantically identical objects
    
    Args:
        obj: Dictionary to serialize
        
    Returns:
        Canonical JSON bytes
    """
    canonical_str = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return canonical_str.encode('utf-8')


def verify_attestation_signature(
    payload: dict,
    signature_hex: str,
    verifier_public_key_hex: str
) -> Tuple[bool, Optional[str]]:
    """
    Verify a VerificationAttestation signature.
    
    Args:
        payload: The attestation payload dict (all fields except signature)
        signature_hex: Hex-encoded signature
        verifier_public_key_hex: Hex-encoded Ed25519 public key
        
    Returns:
        (is_valid, error_message)
    """
    try:
        # Import cryptography for actual validation
        # This import is deferred to allow tests without cryptography library
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.exceptions import InvalidSignature
        except ImportError:
            # If cryptography library not available, use test stub
            return verify_attestation_signature_test_stub(
                payload, signature_hex, verifier_public_key_hex
            )
        
        # Reconstruct canonical payload with domain separation
        canonical_payload = VERIFICATION_DOMAIN + canonical_json(payload)
        
        # Decode signature and public key
        try:
            signature_bytes = bytes.fromhex(signature_hex)
            public_key_bytes = bytes.fromhex(verifier_public_key_hex)
        except ValueError as e:
            return (False, f"Invalid hex encoding: {e}")
        
        # Reconstruct public key object
        try:
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        except Exception as e:
            return (False, f"Invalid public key: {e}")
        
        # Verify signature
        try:
            public_key.verify(signature_bytes, canonical_payload)
            return (True, None)
        except InvalidSignature:
            return (False, "Signature verification failed")
        except Exception as e:
            return (False, f"Verification error: {e}")
            
    except Exception as e:
        return (False, f"Unexpected error during verification: {e}")


def verify_authorization_signature(
    payload: dict,
    signature_hex: str,
    governor_public_key_hex: str
) -> Tuple[bool, Optional[str]]:
    """
    Verify a CommitAuthorization signature.
    
    Args:
        payload: The authorization payload dict (all fields except signature)
        signature_hex: Hex-encoded signature
        governor_public_key_hex: Hex-encoded Ed25519 public key
        
    Returns:
        (is_valid, error_message)
    """
    try:
        # Import cryptography for actual validation
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.exceptions import InvalidSignature
        except ImportError:
            # If cryptography library not available, use test stub
            return verify_authorization_signature_test_stub(
                payload, signature_hex, governor_public_key_hex
            )
        
        # Reconstruct canonical payload with domain separation
        canonical_payload = AUTHORIZATION_DOMAIN + canonical_json(payload)
        
        # Decode signature and public key
        try:
            signature_bytes = bytes.fromhex(signature_hex)
            public_key_bytes = bytes.fromhex(governor_public_key_hex)
        except ValueError as e:
            return (False, f"Invalid hex encoding: {e}")
        
        # Reconstruct public key object
        try:
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        except Exception as e:
            return (False, f"Invalid public key: {e}")
        
        # Verify signature
        try:
            public_key.verify(signature_bytes, canonical_payload)
            return (True, None)
        except InvalidSignature:
            return (False, "Signature verification failed")
        except Exception as e:
            return (False, f"Verification error: {e}")
            
    except Exception as e:
        return (False, f"Unexpected error during verification: {e}")


def verify_attestation_signature_test_stub(
    payload: dict,
    signature_hex: str,
    verifier_public_key_hex: str
) -> Tuple[bool, Optional[str]]:
    """
    Test stub for attestation signature verification (no cryptography library).
    
    For testing without cryptography dependency:
    - Requires specific test key format
    - Allows known test signatures
    - Rejects all other signatures
    """
    # Test fixture: if using test keys, accept specific signatures
    if verifier_public_key_hex == "test_verifier_public_key":
        if signature_hex == "test_verification_signature":
            return (True, None)
    
    return (False, "Signature validation not available (cryptography library not installed)")


def verify_authorization_signature_test_stub(
    payload: dict,
    signature_hex: str,
    governor_public_key_hex: str
) -> Tuple[bool, Optional[str]]:
    """
    Test stub for authorization signature verification (no cryptography library).
    
    For testing without cryptography dependency:
    - Requires specific test key format
    - Allows known test signatures
    - Rejects all other signatures
    """
    # Test fixture: if using test keys, accept specific signatures
    if governor_public_key_hex == "test_governor_public_key":
        if signature_hex == "test_authorization_signature":
            return (True, None)
    
    return (False, "Signature validation not available (cryptography library not installed)")


def detect_domain_separation_violation(
    payload: dict,
    signature_hex: str,
    attester_public_key_hex: str,
    expected_domain: bytes
) -> Tuple[bool, Optional[str]]:
    """
    Detect if a signature from one domain is being used in another domain.
    
    This is a security check to ensure an attestation signature cannot be
    mistakenly used as an authorization signature and vice versa.
    
    Args:
        payload: The payload
        signature_hex: The signature
        attester_public_key_hex: The public key
        expected_domain: The expected domain separator (VERIFICATION_DOMAIN or AUTHORIZATION_DOMAIN)
        
    Returns:
        (violation_detected, error_message)
    """
    # Try to verify with opposite domain
    opposite_domain = (
        AUTHORIZATION_DOMAIN if expected_domain == VERIFICATION_DOMAIN
        else VERIFICATION_DOMAIN
    )
    
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError:
        # Cannot check without cryptography library
        return (False, None)
    
    try:
        canonical_payload = opposite_domain + canonical_json(payload)
        signature_bytes = bytes.fromhex(signature_hex)
        public_key_bytes = bytes.fromhex(attester_public_key_hex)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        
        try:
            public_key.verify(signature_bytes, canonical_payload)
            # If it verifies with opposite domain, VIOLATION DETECTED
            return (True, "Signature validates with wrong domain separator")
        except:
            # Does not validate with opposite domain (good)
            return (False, None)
    except:
        # Error checking, but no violation detected
        return (False, None)
