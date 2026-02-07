import pytest
from datetime import datetime
from ade_compliance.models.axiom import Axiom, Violation, ViolationState, TraceLink
from ade_compliance.models.decision import Decision, Override, Attestation

# === Axiom Model Tests ===

def test_axiom_creation():
    axiom = Axiom(
        id="\u03a3.1",
        name="Specification Primacy",
        category="foundation",
        severity="critical"
    )
    assert axiom.id == "\u03a3.1"
    assert axiom.name == "Specification Primacy"
    assert axiom.enabled is True

def test_axiom_custom_fields():
    axiom = Axiom(
        id="\u03a3.2",
        name="Test Primacy",
        category="verification",
        severity="high",
        enabled=False,
        description="Tests first"
    )
    assert axiom.severity == "high"
    assert axiom.enabled is False
    assert axiom.description == "Tests first"

# === Violation Model Tests ===

def test_violation_state_new():
    violation = Violation(
        axiom_id="\u03a0.1.1",
        file_path="src/foo.py",
        message="No spec found",
    )
    assert violation.state == ViolationState.NEW

def test_violation_acknowledge():
    violation = Violation(
        axiom_id="\u03a0.1.1",
        file_path="src/foo.py",
        message="No spec found",
    )
    violation.acknowledge()
    assert violation.state == ViolationState.ACKNOWLEDGED

def test_violation_resolve():
    violation = Violation(
        axiom_id="\u03a0.1.1",
        file_path="src/foo.py",
        message="No spec found",
    )
    violation.acknowledge()
    violation.resolve()
    assert violation.state == ViolationState.RESOLVED

def test_violation_state_transitions():
    violation = Violation(
        axiom_id="\u03a0.1.1",
        file_path="src/foo.py",
        message="Missing spec",
    )
    assert violation.state == ViolationState.NEW
    violation.acknowledge()
    assert violation.state == ViolationState.ACKNOWLEDGED
    violation.resolve()
    assert violation.state == ViolationState.RESOLVED

def test_violation_override():
    violation = Violation(
        axiom_id="\u03a0.1.1",
        file_path="src/foo.py",
        message="Missing spec",
    )
    violation.acknowledge()
    violation.override()
    assert violation.state == ViolationState.OVERRIDDEN

# === TraceLink Model Tests ===

def test_trace_link():
    link = TraceLink(
        source="src/foo.py",
        target="tests/test_foo.py",
        type="test"
    )
    assert link.source == "src/foo.py"
    assert link.target == "tests/test_foo.py"
    assert link.type == "test"

# === Decision Model Tests ===

def test_decision_requires_human_review_critical():
    decision = Decision(
        axiom_id="\u03a3.1",
        rationale="Requires arch review",
        criticality="critical"
    )
    assert decision.requires_human_review is True

def test_decision_requires_human_review_high():
    decision = Decision(
        axiom_id="\u03a3.1",
        rationale="Complex change",
        criticality="high"
    )
    assert decision.requires_human_review is True

def test_decision_auto_approve_low():
    decision = Decision(
        axiom_id="\u03a3.1",
        rationale="Minor refactor",
        criticality="low"
    )
    assert decision.requires_human_review is False

def test_decision_auto_approve_medium():
    decision = Decision(
        axiom_id="\u03a3.1",
        rationale="Standard change",
        criticality="medium"
    )
    assert decision.requires_human_review is False

# === Override Model Tests ===

def test_override_expiration():
    override = Override(
        axiom_id="\u03a3.2",
        rationale="Temporary exemption",
        criticality="high",
        expires_in_days=90
    )
    assert override.expires_in_days == 90

def test_override_is_active():
    override = Override(
        axiom_id="\u03a3.2",
        rationale="Temporary exemption",
        criticality="high",
    )
    assert override.is_active is True

# === Attestation Model Tests ===

def test_attestation():
    attestation = Attestation(
        agent_id="agent-001",
        task_id="task-001",
        confidence=0.95
    )
    assert attestation.agent_id == "agent-001"
    assert attestation.confidence == 0.95
    assert attestation.timestamp is not None
