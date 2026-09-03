"""
Test Invariant I9: State objects are immutable.
A transition creates a new state rather than secretly mutating the previous state.
"""

import pytest
from cybercognition.states import (
    NeuralState,
    CybercognitiveState,
    DeterministicState,
)
from cybercognition.epistemics import (
    EpistemicStatus,
    Hypothesis,
    VerificationReceipt,
)
from cybercognition.transitions import externalize, refine, verify, commit
from cybercognition.gates import CommitGate


def test_neural_state_frozen():
    """NeuralState is immutable."""
    ns = NeuralState(content="original")
    with pytest.raises((AttributeError, Exception)):
        ns.content = "modified"


def test_cyber_state_frozen():
    """CybercognitiveState is immutable."""
    cs = CybercognitiveState(hypotheses=frozenset(["h1"]))
    with pytest.raises((AttributeError, Exception)):
        cs.hypotheses = frozenset(["h2"])


def test_deterministic_state_frozen():
    """DeterministicState is immutable."""
    ds = DeterministicState(committed_facts=frozenset([("k", "v")]))
    with pytest.raises((AttributeError, Exception)):
        ds.committed_facts = frozenset([("k2", "v2")])


def test_externalize_does_not_mutate_source_neural():
    """externalize() creates a new state; source NeuralState is unchanged."""
    ns_original = NeuralState(content="test", source="src1")
    ns_id = ns_original.id
    ns_content = ns_original.content

    cyber = externalize(ns_original, hypothesis_content="claim")

    # Original neural state unchanged
    assert ns_original.id == ns_id
    assert ns_original.content == ns_content
    assert ns_original.source == "src1"

    # New cyber state is different
    assert cyber.id != ns_id


def test_refine_does_not_mutate_source_cyber():
    """refine() creates a new CybercognitiveState; source is unchanged."""
    cs_original = CybercognitiveState(hypotheses=frozenset(["h1"]))
    cs_id = cs_original.id
    cs_hyp_count = len(cs_original.hypotheses)

    cs_refined = refine(cs_original, updates={"add_hypotheses": ["h2"]})

    # Original unchanged
    assert cs_original.id == cs_id
    assert len(cs_original.hypotheses) == cs_hyp_count
    assert "h2" not in cs_original.hypotheses

    # New state has the update
    assert cs_refined.id != cs_id
    assert "h2" in cs_refined.hypotheses


def test_verify_does_not_mutate_source_cyber():
    """verify() creates a new CybercognitiveState; source is unchanged."""
    cs_original = CybercognitiveState(
        hypotheses=frozenset(["h1"]),
        epistemic_status={"h1": EpistemicStatus.POSSIBLE},
    )
    cs_id = cs_original.id
    original_status = cs_original.epistemic_status["h1"]

    receipt = VerificationReceipt(
        hypothesis_id="h1", verification_method="test"
    )
    cs_verified = verify(cs_original, "h1", receipt)

    # Original unchanged
    assert cs_original.id == cs_id
    assert cs_original.epistemic_status["h1"] == original_status
    assert cs_original.epistemic_status["h1"] == EpistemicStatus.POSSIBLE

    # New state has verification
    assert cs_verified.id != cs_id
    assert cs_verified.epistemic_status["h1"] == EpistemicStatus.VERIFIED


def test_commit_does_not_mutate_source_cyber():
    """commit() creates a new DeterministicState; source CybercognitiveState unchanged."""
    cs_original = CybercognitiveState(
        hypotheses=frozenset(["h1"]),
        epistemic_status={"h1": EpistemicStatus.VERIFIED},
        metadata={
            "receipt_h1": VerificationReceipt(
                hypothesis_id="h1", verification_method="test"
            )
        },
    )
    cs_id = cs_original.id

    gate = CommitGate(
        hypotheses_to_commit=frozenset(["h1"]),
        required_receipts=frozenset(["receipt_1"]),
    )
    det = commit(cs_original, gate)

    # Original CybercognitiveState unchanged
    assert cs_original.id == cs_id
    assert isinstance(cs_original, CybercognitiveState)
    # No new attributes added
    assert "committed_facts" not in dir(cs_original)

    # New DeterministicState is separate
    assert det.id != cs_id
    assert isinstance(det, DeterministicState)
    assert det.source_cyber_id == cs_id


def test_state_chain_maintains_immutability():
    """
    Full transition chain: externalize -> refine -> verify -> commit.
    Each step creates new objects; no mutation along the chain.
    """
    from cybercognition.states import NeuralState

    ns = NeuralState(content="model output")
    ns_id = ns.id

    cs1 = externalize(ns, hypothesis_content="claim 1")
    cs1_id = cs1.id
    h1 = list(cs1.hypotheses)[0]

    cs2 = refine(cs1, updates={"add_hypotheses": ["h2"]})
    cs2_id = cs2.id

    receipt = VerificationReceipt(hypothesis_id=h1, verification_method="test")
    cs3 = verify(cs2, h1, receipt)
    cs3_id = cs3.id

    gate = CommitGate(
        hypotheses_to_commit=frozenset([h1]),
        required_receipts=frozenset([receipt.id]),
    )
    ds = commit(cs3, gate)
    ds_id = ds.id

    # All objects are unique and unchanged
    assert len({ns_id, cs1_id, cs2_id, cs3_id, ds_id}) == 5
    # Original neural state is still there and unchanged
    assert ns.id == ns_id
    assert ns.content == "model output"
