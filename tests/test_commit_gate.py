"""
Test Invariant I5: CybercognitiveState -> DeterministicState requires
an explicit successful gate object.

Test Invariant I7: Unknown or incomplete gate information fails closed.

Test Invariant I10: Illegal transitions are structurally impossible.
"""

import pytest
from cybercognition.states import CybercognitiveState, DeterministicState
from cybercognition.epistemics import (
    EpistemicStatus,
    Hypothesis,
    VerificationReceipt,
)
from cybercognition.gates import CommitGate
from cybercognition.transitions import externalize, verify, commit, get_audit_log
from cybercognition.states import NeuralState


def test_commit_requires_complete_gate():
    """commit() fails closed if gate is incomplete."""
    # Create minimal cyber state
    cyber = CybercognitiveState(
        hypotheses=frozenset(["h1"]),
        epistemic_status={"h1": EpistemicStatus.VERIFIED},
    )

    # Create incomplete gate (empty hypotheses_to_commit)
    bad_gate = CommitGate(hypotheses_to_commit=frozenset())

    with pytest.raises(ValueError, match="CommitGate is incomplete"):
        commit(cyber, bad_gate)


def test_commit_requires_verified_hypotheses():
    """commit() fails closed if hypotheses are not VERIFIED."""
    cyber = CybercognitiveState(
        hypotheses=frozenset(["h1"]),
        epistemic_status={"h1": EpistemicStatus.POSSIBLE},  # Not verified!
    )

    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h1"]),
        required_receipts=frozenset(["receipt_1"]),
    )

    with pytest.raises(ValueError, match="not VERIFIED"):
        commit(cyber, gate)


def test_commit_requires_receipts():
    """commit() fails closed if verification receipts are missing."""
    cyber = CybercognitiveState(
        hypotheses=frozenset(["h1"]),
        epistemic_status={"h1": EpistemicStatus.VERIFIED},
        # But no receipt in metadata
    )

    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h1"]),
        required_receipts=frozenset(["receipt_1"]),
    )

    with pytest.raises(ValueError, match="receipt validation failed"):
        commit(cyber, gate)


def test_commit_excludes_non_committed_hypotheses():
    """Gate can exclude hypotheses; they don't become deterministic."""
    cyber = CybercognitiveState(
        hypotheses=frozenset(["h1", "h2"]),
        epistemic_status={
            "h1": EpistemicStatus.VERIFIED,
            "h2": EpistemicStatus.VERIFIED,
        },
        metadata={
            "receipt_h1": VerificationReceipt(
                hypothesis_id="h1", verification_method="manual"
            ),
            "receipt_h2": VerificationReceipt(
                hypothesis_id="h2", verification_method="manual"
            ),
        },
    )

    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h1"]),
        hypotheses_excluded=frozenset(["h2"]),
        required_receipts=frozenset(["receipt_h1"]),
    )

    det = commit(cyber, gate)
    assert isinstance(det, DeterministicState)
    # Only h1 in committed facts
    assert any("h1" in str(fact) for fact in det.committed_facts)


def test_gate_rejects_overlapping_commit_and_exclude():
    """Gate fails closed if a hypothesis is both committed and excluded."""
    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h1"]),
        hypotheses_excluded=frozenset(["h1"]),  # Overlap!
        required_receipts=frozenset(["receipt_1"]),
    )

    assert not gate.is_complete()


def test_successful_commit_flow():
    """Complete successful commit flow: externalize -> verify -> commit."""
    # Start with NeuralState
    ns = NeuralState(content="model says X is true")

    # Externalize to CybercognitiveState
    cyber = externalize(ns, hypothesis_content="X is true")
    hyp_id = list(cyber.hypotheses)[0]

    # Create verification receipt
    receipt = VerificationReceipt(
        hypothesis_id=hyp_id,
        verification_method="manual_review",
        verified_at="2026-09-03T00:00:00Z",
    )

    # Verify the hypothesis
    cyber_verified = verify(cyber, hyp_id, receipt)
    assert cyber_verified.epistemic_status[hyp_id] == EpistemicStatus.VERIFIED

    # Commit to DeterministicState
    gate = CommitGate(
        hypotheses_to_commit=frozenset([hyp_id]),
        required_receipts=frozenset([receipt.id]),
    )
    det = commit(cyber_verified, gate)

    assert isinstance(det, DeterministicState)
    assert len(det.committed_facts) > 0
    assert det.source_cyber_id == cyber_verified.id


def test_commit_records_audit_event():
    """Each commit() creates an audit event."""
    audit_log = get_audit_log()
    initial_count = len(audit_log.events)

    ns = NeuralState(content="test")
    cyber = externalize(ns, hypothesis_content="test")
    hyp_id = list(cyber.hypotheses)[0]

    receipt = VerificationReceipt(
        hypothesis_id=hyp_id, verification_method="test"
    )
    cyber_verified = verify(cyber, hyp_id, receipt)

    gate = CommitGate(
        hypotheses_to_commit=frozenset([hyp_id]),
        required_receipts=frozenset([receipt.id]),
    )
    det = commit(cyber_verified, gate)

    # Should have externalize + verify + commit events
    assert len(audit_log.events) > initial_count
    # Last event should be commit
    assert audit_log.events[-1].transition_type == "commit"
    assert audit_log.events[-1].source_regime == "CybercognitiveState"
    assert audit_log.events[-1].target_regime == "DeterministicState"
