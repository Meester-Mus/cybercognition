"""
Test Invariant I3: NeuralState may only produce a CybercognitiveState
candidate through an explicit externalization transition.

Also test Invariant I9: State objects are immutable, and transitions
create new objects without mutating the source.
"""

import pytest
from cybercognition.states import NeuralState, CybercognitiveState
from cybercognition.epistemics import EpistemicStatus
from cybercognition.transitions import externalize, get_audit_log


def test_externalize_neural_to_cyber():
    """externalize() transitions NeuralState -> CybercognitiveState."""
    ns = NeuralState(content="model prediction", source="model_v1")
    cyber = externalize(ns, hypothesis_content="X is likely true")

    assert isinstance(cyber, CybercognitiveState)
    assert len(cyber.hypotheses) == 1
    assert cyber.provenance.startswith("external(")


def test_externalize_sets_hypothesis_to_possible():
    """The externalized hypothesis starts in POSSIBLE status."""
    ns = NeuralState(content="claim")
    cyber = externalize(ns, hypothesis_content="claim text")

    # Extract the hypothesis id from the frozen set
    hyp_id = list(cyber.hypotheses)[0]
    assert cyber.epistemic_status[hyp_id] == EpistemicStatus.POSSIBLE


def test_externalize_does_not_mutate_source():
    """externalize() creates a new CybercognitiveState without mutating NeuralState."""
    ns = NeuralState(content="original", source="src1")
    ns_id_before = ns.id
    ns_content_before = ns.content

    cyber = externalize(ns, hypothesis_content="new claim")

    # Original NeuralState unchanged
    assert ns.id == ns_id_before
    assert ns.content == ns_content_before
    # New state is different
    assert cyber.id != ns.id


def test_externalize_records_audit_event():
    """Each externalize() creates an audit event."""
    audit_log = get_audit_log()
    initial_count = len(audit_log.events)

    ns = NeuralState(content="test")
    cyber = externalize(ns, hypothesis_content="test claim")

    assert len(audit_log.events) == initial_count + 1
    event = audit_log.events[-1]
    assert event.transition_type == "externalize"
    assert event.source_regime == "NeuralState"
    assert event.target_regime == "CybercognitiveState"
    assert event.source_id == ns.id
    assert event.target_id == cyber.id


def test_no_direct_neural_to_cyber_without_function():
    """
    There is no public API function to skip externalize().
    (This is enforced by the absence of such functions in the public API.)
    """
    # The only way to create CybercognitiveState from NeuralState is via externalize()
    # This test documents the design: we do not provide a direct constructor bypass.
    ns = NeuralState(content="test")
    # No way to bypass externalize() through public API
    cyber = externalize(ns, hypothesis_content="test")
    assert isinstance(cyber, CybercognitiveState)
