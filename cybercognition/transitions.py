"""
State transition functions: the only legal ways to move between regimes.

Invariant I2: There MUST NOT be any direct NeuralState -> DeterministicState transition.
Invariant I3: NeuralState may only produce a CybercognitiveState candidate
             through an explicit externalization transition.
Invariant I5: CybercognitiveState -> DeterministicState requires an explicit
             successful gate object.
Invariant I10: The architecture must make illegal transitions structurally
              difficult or impossible through its public API.
"""

from dataclasses import replace
from typing import Optional, Dict

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
from cybercognition.gates import CommitGate
from cybercognition.audit import AuditEvent, AuditLog

# Global audit log for all transitions
_global_audit_log = AuditLog()


def get_audit_log() -> AuditLog:
    """Retrieve the global audit log."""
    return _global_audit_log


def externalize(
    neural_state: NeuralState,
    hypothesis_content: str,
    source_label: Optional[str] = None,
) -> CybercognitiveState:
    """
    Transition: NeuralState -> CybercognitiveState

    Invariant I3: NeuralState may only produce a CybercognitiveState candidate
    through an explicit externalization transition.

    Creates a CybercognitiveState with a single POSSIBLE hypothesis,
    tracing provenance back to the NeuralState.

    Args:
        neural_state: Source NeuralState
        hypothesis_content: The externalized claim
        source_label: Optional label for provenance

    Returns:
        New CybercognitiveState with the hypothesis in POSSIBLE status
    """
    hyp = Hypothesis(
        content=hypothesis_content,
        status=EpistemicStatus.POSSIBLE,
        metadata={"source_neural": neural_state.id},
    )

    cyber_state = CybercognitiveState(
        hypotheses=frozenset([hyp.id]),
        provenance=f"external({neural_state.id})",
        epistemic_status={hyp.id: EpistemicStatus.POSSIBLE},
        metadata={
            "hypothesis_objects": {hyp.id: hyp},
            "source_neural_id": neural_state.id,
        },
    )

    # Record audit event
    event = AuditEvent(
        transition_type="externalize",
        source_regime="NeuralState",
        target_regime="CybercognitiveState",
        source_id=neural_state.id,
        target_id=cyber_state.id,
        provenance=neural_state.id,
    )
    _global_audit_log.record(event)

    return cyber_state


def refine(
    cyber_state: CybercognitiveState,
    updates: Optional[Dict] = None,
) -> CybercognitiveState:
    """
    Transition: CybercognitiveState -> CybercognitiveState

    Applies refinements (new hypotheses, evidence, bindings, open work)
    without changing epistemic status or committing anything.

    Invariant I4: May contain unresolved/open/provisional states.
    Invariant I9: Immutable. Creates a new state object.

    Args:
        cyber_state: Source CybercognitiveState
        updates: Dict with keys like 'add_hypotheses', 'add_evidence',
                'add_discrepancies', 'add_open_work'

    Returns:
        New CybercognitiveState with updates applied
    """
    if updates is None:
        updates = {}

    new_hypotheses = set(cyber_state.hypotheses)
    new_evidence = set(cyber_state.evidence)
    new_discrepancies = set(cyber_state.discrepancies)
    new_open_work = set(cyber_state.open_work)
    new_bindings = set(cyber_state.bindings)

    # Merge in updates
    if "add_hypotheses" in updates:
        new_hypotheses.update(updates["add_hypotheses"])
    if "add_evidence" in updates:
        new_evidence.update(updates["add_evidence"])
    if "add_discrepancies" in updates:
        new_discrepancies.update(updates["add_discrepancies"])
    if "add_open_work" in updates:
        new_open_work.update(updates["add_open_work"])
    if "add_bindings" in updates:
        new_bindings.update(updates["add_bindings"])

    refined = replace(
        cyber_state,
        hypotheses=frozenset(new_hypotheses),
        evidence=frozenset(new_evidence),
        discrepancies=frozenset(new_discrepancies),
        open_work=frozenset(new_open_work),
        bindings=frozenset(new_bindings),
    )

    # Record audit event
    event = AuditEvent(
        transition_type="refine",
        source_regime="CybercognitiveState",
        target_regime="CybercognitiveState",
        source_id=cyber_state.id,
        target_id=refined.id,
        provenance=cyber_state.id,
    )
    _global_audit_log.record(event)

    return refined


def verify(
    cyber_state: CybercognitiveState,
    hypothesis_id: str,
    receipt: VerificationReceipt,
) -> CybercognitiveState:
    """
    Transition: CybercognitiveState -> CybercognitiveState with verification

    Invariant I6: A model assertion such as "X is verified" MUST NOT itself
    produce verified or deterministic state. Verification is a transition.

    Updates the epistemic status of a hypothesis to VERIFIED and records
    the verification receipt. Does NOT commit to DeterministicState.

    Args:
        cyber_state: Source CybercognitiveState
        hypothesis_id: Which hypothesis to verify
        receipt: VerificationReceipt recording the verification

    Returns:
        New CybercognitiveState with updated epistemic status
    """
    if hypothesis_id not in cyber_state.hypotheses:
        raise ValueError(f"Hypothesis {hypothesis_id} not in state")

    new_status = dict(cyber_state.epistemic_status)
    new_status[hypothesis_id] = EpistemicStatus.VERIFIED

    verified = replace(
        cyber_state,
        epistemic_status=new_status,
        metadata={
            **cyber_state.metadata,
            f"receipt_{hypothesis_id}": receipt,
        },
    )

    # Record audit event
    event = AuditEvent(
        transition_type="verify",
        source_regime="CybercognitiveState",
        target_regime="CybercognitiveState",
        source_id=cyber_state.id,
        target_id=verified.id,
        provenance=receipt.id,
    )
    _global_audit_log.record(event)

    return verified


def commit(
    cyber_state: CybercognitiveState,
    gate: CommitGate,
) -> DeterministicState:
    """
    Transition: CybercognitiveState -> DeterministicState

    Invariant I2: There MUST NOT be any direct NeuralState -> DeterministicState.
    Invariant I5: CybercognitiveState -> DeterministicState requires an explicit
                  successful gate object.
    Invariant I7: Unknown or incomplete gate information fails closed.

    Args:
        cyber_state: Source CybercognitiveState
        gate: CommitGate specifying what to commit

    Returns:
        New DeterministicState

    Raises:
        ValueError: If gate is incomplete, receipts missing, or verification lacking
    """
    # Fail closed: check gate completeness
    if not gate.is_complete():
        raise ValueError("CommitGate is incomplete: fails closed")

    # Fail closed: check all hypotheses to commit are verified
    status_dict = cyber_state.epistemic_status or {}
    for hyp_id in gate.hypotheses_to_commit:
        if hyp_id not in status_dict:
            raise ValueError(
                f"Hypothesis {hyp_id} not in epistemic_status: fails closed"
            )
        if status_dict[hyp_id] != EpistemicStatus.VERIFIED:
            raise ValueError(
                f"Hypothesis {hyp_id} not VERIFIED (status={status_dict[hyp_id]}): "
                "fails closed"
            )

    # Fail closed: check gate can validate receipts
    receipts_by_hyp = {}
    for hyp_id in gate.hypotheses_to_commit:
        receipt_key = f"receipt_{hyp_id}"
        receipts_by_hyp[hyp_id] = cyber_state.metadata.get(receipt_key)

    if not gate.validate_receipts(receipts_by_hyp):
        raise ValueError("Gate receipt validation failed: fails closed")

    # Build committed facts: (key, value) pairs
    committed_facts = set()
    for hyp_id in gate.hypotheses_to_commit:
        # Simple representation: (hyp_id, "committed")
        committed_facts.add((hyp_id, "committed"))

    det_state = DeterministicState(
        committed_facts=frozenset(committed_facts),
        provenance=f"gate({gate.id})",
        source_cyber_id=cyber_state.id,
        verification_chain=frozenset(gate.required_receipts),
    )

    # Record audit event
    event = AuditEvent(
        transition_type="commit",
        source_regime="CybercognitiveState",
        target_regime="DeterministicState",
        source_id=cyber_state.id,
        target_id=det_state.id,
        provenance=gate.id,
    )
    _global_audit_log.record(event)

    return det_state
