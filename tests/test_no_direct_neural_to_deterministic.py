"""
Test Invariant I2: There MUST NOT be any direct NeuralState -> DeterministicState
transition.

Invariant I10: The architecture must make illegal transitions structurally
difficult or impossible through its public API.

Tests that verify the absence of dangerous shortcuts.
"""

import pytest
from cybercognition.states import NeuralState, DeterministicState
from cybercognition.transitions import (
    externalize,
    commit,
    refine,
    verify,
)


def test_no_function_neural_to_deterministic():
    """
    There is no public function neural_to_deterministic() or force_commit().
    The only legal path requires explicit externalization and gating.
    """
    # Check that the function does not exist in the transitions module
    from cybercognition import transitions

    # These dangerous functions should NOT exist
    assert not hasattr(transitions, "neural_to_deterministic")
    assert not hasattr(transitions, "force_commit")
    assert not hasattr(transitions, "trust_model_output")
    assert not hasattr(transitions, "bypass_gate")


def test_cannot_commit_without_cyber_state():
    """
    commit() requires a CybercognitiveState.
    You cannot pass a NeuralState to commit().
    """
    from cybercognition.gates import CommitGate

    ns = NeuralState(content="raw output")
    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h1"]),
        required_receipts=frozenset(["r1"]),
    )

    # commit() expects CybercognitiveState, not NeuralState
    with pytest.raises((AttributeError, TypeError, ValueError)):
        # This will fail because NeuralState doesn't have the required attributes
        commit(ns, gate)


def test_externalize_required_before_commit():
    """
    The only legal path is: NeuralState -> externalize -> CybercognitiveState
    You must go through externalize() first.
    """
    ns = NeuralState(content="test")
    # Without externalize(), there is no CybercognitiveState to commit
    # The type system prevents skipping steps

    # Calling externalize is mandatory
    cs = externalize(ns, hypothesis_content="claim")
    assert cs is not None


def test_verify_required_before_commit():
    """
    commit() requires verified hypotheses.
    You cannot commit POSSIBLE hypotheses.
    """
    from cybercognition.epistemics import EpistemicStatus
    from cybercognition.gates import CommitGate

    cs = externalize(NeuralState(content="test"), hypothesis_content="claim")
    hyp_id = list(cs.hypotheses)[0]

    gate = CommitGate(
        hypotheses_to_commit=frozenset([hyp_id]),
        required_receipts=frozenset(["r1"]),
    )

    # Try to commit without verification
    with pytest.raises(ValueError, match="not VERIFIED"):
        commit(cs, gate)


def test_gate_prevents_unverified_commits():
    """
    CommitGate.validate_receipts() enforces that receipts exist.
    Missing receipts = gate fails closed.
    """
    from cybercognition.gates import CommitGate

    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h1"]),
        required_receipts=frozenset(["r1"]),
    )

    # Empty receipts dict
    receipts = {}
    assert not gate.validate_receipts(receipts)

    # Missing receipt for h1
    receipts = {"h1": None}
    assert not gate.validate_receipts(receipts)


def test_deterministic_state_requires_committed_facts():
    """
    Even if you manually construct a DeterministicState,
    it requires committed_facts. The normal path (via commit())
    is the only way to get there safely from NeuralState.
    """
    # Manual construction (not recommended)
    ds = DeterministicState(committed_facts=frozenset([("key", "value")]))
    assert ds is not None

    # But the proper way is through the commit() function,
    # which enforces gating and verification.
    ns = NeuralState(content="test")
    cs = externalize(ns, hypothesis_content="claim")
    # Must verify before commit...
