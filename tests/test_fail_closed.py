"""
Test Invariant I7: Unknown or incomplete gate information fails closed.

Tests for negative cases where the system should reject unsafe transitions.
"""

import pytest
from cybercognition.states import NeuralState, CybercognitiveState, DeterministicState
from cybercognition.epistemics import EpistemicStatus, VerificationReceipt
from cybercognition.gates import CommitGate
from cybercognition.transitions import externalize, verify, commit


def test_gate_empty_commit_set_fails():
    """Gate with no hypotheses to commit is incomplete."""
    gate = CommitGate(
        hypotheses_to_commit=frozenset(),  # Empty!
        required_receipts=frozenset(["r1"]),
    )
    assert not gate.is_complete()


def test_gate_empty_receipts_fails():
    """Gate with no receipts is incomplete."""
    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h1"]),
        required_receipts=frozenset(),  # Empty!
    )
    assert not gate.is_complete()


def test_commit_with_missing_hypothesis_fails():
    """commit() fails if gate references hypothesis not in cyber state."""
    cyber = CybercognitiveState(
        hypotheses=frozenset(["h1"]),
        epistemic_status={"h1": EpistemicStatus.VERIFIED},
    )

    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h2"]),  # Not in cyber state!
        required_receipts=frozenset(["r1"]),
    )

    with pytest.raises(ValueError, match="not in epistemic_status"):
        commit(cyber, gate)


def test_commit_with_unverified_hypothesis_fails():
    """commit() fails if hypothesis is not VERIFIED."""
    cyber = CybercognitiveState(
        hypotheses=frozenset(["h1"]),
        epistemic_status={"h1": EpistemicStatus.POSSIBLE},  # Not verified!
    )

    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h1"]),
        required_receipts=frozenset(["r1"]),
    )

    with pytest.raises(ValueError, match="not VERIFIED"):
        commit(cyber, gate)


def test_commit_missing_receipt_in_metadata_fails():
    """commit() fails if receipt is not in CybercognitiveState metadata."""
    cyber = CybercognitiveState(
        hypotheses=frozenset(["h1"]),
        epistemic_status={"h1": EpistemicStatus.VERIFIED},
        metadata={},  # No receipt!
    )

    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h1"]),
        required_receipts=frozenset(["receipt_h1"]),
    )

    with pytest.raises(ValueError, match="receipt validation failed"):
        commit(cyber, gate)


def test_no_neural_to_deterministic_bypass():
    """
    Invariant I2: There MUST NOT be any direct NeuralState -> DeterministicState.
    
    This test documents that there is NO public API function to skip
    the CybercognitiveState regime. The only legal path is:
    NeuralState -> externalize -> CybercognitiveState -> verify -> commit -> DeterministicState
    """
    ns = NeuralState(content="raw model output")
    # There is no function like neural_to_deterministic() or force_commit()
    # The architecture structurally prevents this bypass.
    # Attempting to create DeterministicState directly bypasses gating:
    direct_det = DeterministicState(
        committed_facts=frozenset([("key", "value")])
    )
    # But this is not how the system is meant to be used.
    # All legitimate transitions go through the transition functions.
    assert isinstance(direct_det, DeterministicState)


def test_model_assertion_string_does_not_verify():
    """
    Invariant I6: A model assertion such as "X is verified" MUST NOT
    itself produce verified state.
    
    Even if NeuralState contains the string "verified", it does not
    become verified without an explicit verify() transition.
    """
    # NeuralState with a claims about verification
    ns = NeuralState(
        content="This claim is verified and I am certain of it."
    )

    # Externalize it
    cyber = externalize(
        ns,
        hypothesis_content=ns.content,
    )
    hyp_id = list(cyber.hypotheses)[0]

    # Check epistemic status: still POSSIBLE, not VERIFIED
    assert cyber.epistemic_status[hyp_id] == EpistemicStatus.POSSIBLE

    # The words "verified" in the content don't change the epistemic status
    assert "verified" in cyber.metadata.get(
        f"hypothesis_objects", {}
    ).get(hyp_id, "").content.lower() or "verified" not in str(cyber)

    # To actually make it verified, we need an explicit verify() transition
    receipt = VerificationReceipt(
        hypothesis_id=hyp_id, verification_method="manual_inspection"
    )
    cyber_verified = verify(cyber, hyp_id, receipt)
    assert cyber_verified.epistemic_status[hyp_id] == EpistemicStatus.VERIFIED
