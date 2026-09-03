"""
Test Invariant I1: NeuralState != CybercognitiveState != DeterministicState

Ensure the three regimes are distinct and that objects retain their type identity.
"""

import pytest
from cybercognition.states import (
    NeuralState,
    CybercognitiveState,
    DeterministicState,
)


def test_state_types_are_distinct():
    """Each state type is a distinct class."""
    ns = NeuralState(content="model output")
    cs = CybercognitiveState(hypotheses=frozenset(["h1"]))
    ds = DeterministicState(committed_facts=frozenset([("key", "value")]))

    assert type(ns) is NeuralState
    assert type(cs) is CybercognitiveState
    assert type(ds) is DeterministicState

    assert not isinstance(ns, CybercognitiveState)
    assert not isinstance(ns, DeterministicState)
    assert not isinstance(cs, NeuralState)
    assert not isinstance(cs, DeterministicState)
    assert not isinstance(ds, NeuralState)
    assert not isinstance(ds, CybercognitiveState)


def test_neural_state_immutable():
    """NeuralState is frozen (immutable)."""
    ns = NeuralState(content="test")
    with pytest.raises(AttributeError):
        ns.content = "modified"


def test_cyber_state_immutable():
    """CybercognitiveState is frozen (immutable)."""
    cs = CybercognitiveState(hypotheses=frozenset(["h1"]))
    with pytest.raises(AttributeError):
        cs.hypotheses = frozenset(["h2"])


def test_deterministic_state_immutable():
    """DeterministicState is frozen (immutable)."""
    ds = DeterministicState(committed_facts=frozenset([("k", "v")]))
    with pytest.raises(AttributeError):
        ds.committed_facts = frozenset([("k2", "v2")])


def test_each_state_has_unique_id():
    """Each state instance gets a unique id."""
    ns1 = NeuralState(content="a")
    ns2 = NeuralState(content="b")
    assert ns1.id != ns2.id

    cs1 = CybercognitiveState()
    cs2 = CybercognitiveState()
    assert cs1.id != cs2.id

    ds1 = DeterministicState()
    ds2 = DeterministicState()
    assert ds1.id != ds2.id
