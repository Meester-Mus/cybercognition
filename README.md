# Cybercognition: Minimal Falsifiable Kernel

A minimal Python 3 package implementing the cognitive-computer architecture hypothesis:

```
NeuralState <> CybercognitiveState | DeterministicState
```

## Architecture

### Three Distinct State Regimes

**1. NeuralState**
- Represents output from probabilistic/neural cognition
- Contains candidates, scores, observations, opaque model-derived material
- Is NOT verified truth
- Has NO authority to create DeterministicState

**2. CybercognitiveState**
- First-class explicit intermediate cognitive regime
- Contains: hypotheses, bindings, evidence, provenance, open work, discrepancies, epistemic status
- May be explicit while unresolved, provisional, conflicting, or incomplete
- Prevents premature conversion of probabilistic cognition to deterministic commitment

**3. DeterministicState**
- Contains only explicitly committed deterministic state
- Transitions gated and audited
- No probabilistic output may directly instantiate or mutate it

## Core Invariants

- **I1**: NeuralState ≠ CybercognitiveState ≠ DeterministicState (distinct types)
- **I2**: No direct NeuralState → DeterministicState (prevented by public API)
- **I3**: NeuralState → CybercognitiveState only via explicit `externalize()` transition
- **I4**: CybercognitiveState may contain unresolved/provisional/conflicting states without forcing commitment
- **I5**: CybercognitiveState → DeterministicState requires explicit successful `CommitGate`
- **I6**: Model assertions (e.g., "X is verified") don't produce verified state without explicit transition
- **I7**: Unknown or incomplete gate information fails closed
- **I8**: All state transitions auditable
- **I9**: State objects immutable; transitions create new objects
- **I10**: Illegal transitions structurally impossible through public API

## Package Structure

```
cybercognition/
  __init__.py        # Public API
  states.py          # NeuralState, CybercognitiveState, DeterministicState
  epistemics.py      # Hypothesis, Binding, Evidence, Provenance, etc.
  gates.py           # CommitGate gating mechanism
  transitions.py     # externalize, refine, verify, commit functions
  audit.py           # AuditEvent, AuditLog
tests/
  test_state_separation.py          # I1, I9: distinct types, immutability
  test_externalization.py           # I3, I9: externalize transitions
  test_commit_gate.py               # I5, I7: gating and fail-closed
  test_fail_closed.py               # I6, I7: negative test cases
  test_immutability.py              # I9: immutability chain
  test_no_direct_neural_to_deterministic.py  # I2, I10: prevent shortcuts
```

## Core API

### Transitions

```python
from cybercognition import (
    NeuralState, CybercognitiveState, DeterministicState,
    externalize, refine, verify, commit,
    CommitGate, VerificationReceipt, EpistemicStatus
)

# Step 1: Create NeuralState (from a model or probabilistic source)
neural = NeuralState(content="model output", source="model_v1")

# Step 2: Externalize to CybercognitiveState
cyber = externalize(neural, hypothesis_content="X is likely true")

# Step 3: Refine the CybercognitiveState with evidence, open work, etc.
cyber = refine(cyber, updates={
    "add_evidence": ["evidence_1"],
    "add_open_work": ["verify_X_independently"]
})

# Step 4: Create a verification receipt (manual, test suite, etc.)
receipt = VerificationReceipt(
    hypothesis_id="h1",
    verification_method="manual_review"
)

# Step 5: Verify the hypothesis (explicit transition)
cyber = verify(cyber, hypothesis_id="h1", receipt=receipt)

# Step 6: Create a commit gate (specifies what to commit)
gate = CommitGate(
    hypotheses_to_commit=frozenset(["h1"]),
    required_receipts=frozenset([receipt.id])
)

# Step 7: Commit to DeterministicState (fails closed if incomplete)
deterministic = commit(cyber, gate)
```

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Negative Tests (Fail-Closed Validation)

The test suite includes mandatory negative tests:

1. **Direct NeuralState → DeterministicState**: Impossible through public API
2. **Model assertion as verification**: String "verified" in NeuralState doesn't verify
3. **Commit without verification**: Fails closed if epistemic_status != VERIFIED
4. **Incomplete gate**: Fails closed if gate lacks hypotheses or receipts
5. **Conflicting hypotheses**: Both can coexist in CybercognitiveState
6. **Verified hypothesis preservation**: Unverified hypotheses not auto-deleted
7. **Immutability chain**: Source states unchanged after transitions
8. **Audit trail**: All transitions recorded

## Design Philosophy

**CybercognitiveState is not middleware.** It is a first-class computational regime where cognition can be explicit without yet being deterministic or committed. This prevents the architecture from collapsing probabilistic uncertainty into false certainty prematurely.

**Gating is structural, not optional.** The `CommitGate` mechanism is enforced at the type and function level. There is no way to bypass it through the public API.

**Fail closed by default.** Unknown or incomplete information causes transitions to reject, not to assume defaults.

## Files

- `cybercognition/states.py`: Core state types (frozen dataclasses)
- `cybercognition/epistemics.py`: Knowledge representation (Hypothesis, Evidence, etc.)
- `cybercognition/gates.py`: CommitGate with validation logic
- `cybercognition/transitions.py`: Transition functions + global audit log
- `cybercognition/audit.py`: AuditEvent and AuditLog
- `tests/test_*.py`: Comprehensive test suite covering all invariants

## License

MIT
