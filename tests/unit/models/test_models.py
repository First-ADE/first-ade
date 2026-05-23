"""Unit tests for domain models: Axiom, Violation, Decision, Override, Attestation.

Covers state machine transitions, type-safety constraints, enum validation,
and backward-compatible string coercion.
"""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from ade_compliance.models.axiom import (
    Axiom,
    InvalidStateTransition,
    Severity,
    TraceLink,
    Violation,
    ViolationState,
)
from ade_compliance.models.decision import (
    Attestation,
    AttestationStatus,
    Criticality,
    Decision,
    Override,
    ScopeType,
)

# ── Axiom ──────────────────────────────────────────────────────────────


def test_axiom_creation():
    axiom = Axiom(id="Π.1.1", name="Spec Governance", category="SPECIFICATION", severity="high")
    assert axiom.id == "Π.1.1"
    assert axiom.enabled is True


# ── Violation State Machine ────────────────────────────────────────────


def test_violation_state_machine():
    v = Violation(axiom_id="Π.1.1", file_path="src/main.py", message="No spec")
    assert v.state == ViolationState.NEW
    assert v.resolved_at is None

    v.acknowledge()
    assert v.state == ViolationState.ACKNOWLEDGED

    v.resolve()
    assert v.state == ViolationState.RESOLVED
    assert v.resolved_at is not None


def test_violation_cannot_resolve_from_new():
    """Resolving directly from NEW is not allowed (must acknowledge first)."""
    v = Violation(axiom_id="Π.1.1", file_path="src/main.py", message="No spec")
    with pytest.raises(InvalidStateTransition, match="must be 'acknowledged'"):
        v.resolve()


def test_violation_cannot_acknowledge_from_resolved():
    """RESOLVED is terminal — no backward transitions."""
    v = Violation(axiom_id="Π.1.1", file_path="src/main.py", message="No spec")
    v.acknowledge()
    v.resolve()
    with pytest.raises(InvalidStateTransition, match="must be 'new'"):
        v.acknowledge()


def test_violation_override_from_new():
    """Override should work from NEW state."""
    v = Violation(axiom_id="Π.1.1", file_path="src/main.py", message="No spec")
    v.override()
    assert v.state == ViolationState.OVERRIDDEN
    assert v.resolved_at is not None


def test_violation_override_from_acknowledged():
    """Override should work from ACKNOWLEDGED state."""
    v = Violation(axiom_id="Π.1.1", file_path="src/main.py", message="No spec")
    v.acknowledge()
    v.override()
    assert v.state == ViolationState.OVERRIDDEN


def test_violation_cannot_override_from_resolved():
    """Cannot override from RESOLVED (terminal state)."""
    v = Violation(axiom_id="Π.1.1", file_path="src/main.py", message="No spec")
    v.acknowledge()
    v.resolve()
    with pytest.raises(InvalidStateTransition, match="terminal state"):
        v.override()


def test_violation_cannot_override_twice():
    """Cannot override from OVERRIDDEN (terminal state)."""
    v = Violation(axiom_id="Π.1.1", file_path="src/main.py", message="No spec")
    v.override()
    with pytest.raises(InvalidStateTransition, match="terminal state"):
        v.override()


def test_violation_severity_enum_coercion():
    """String severity values are coerced to the Severity enum."""
    v = Violation(axiom_id="X", file_path="f.py", message="m", severity="high")
    assert v.severity == Severity.HIGH
    assert isinstance(v.severity, Severity)


def test_violation_default_severity():
    """Default severity should be Severity.MEDIUM."""
    v = Violation(axiom_id="X", file_path="f.py", message="m")
    assert v.severity == Severity.MEDIUM


# ── TraceLink ──────────────────────────────────────────────────────────


def test_tracelink_matrix():
    link = TraceLink(source="src/main.py", target="tests/test_main.py", type="validates")
    assert link.source == "src/main.py"


# ── Decision ───────────────────────────────────────────────────────────


def test_decision_criticality():
    d = Decision(axiom_id="Π.5.3", rationale="Test", criticality="critical")
    assert d.requires_human_review is True
    assert isinstance(d.criticality, Criticality)


def test_decision_low_criticality_auto_approved():
    """Low/medium criticality should NOT require human review."""
    d = Decision(axiom_id="Π.1.1", rationale="Test", criticality="low")
    assert d.requires_human_review is False


# ── Override ───────────────────────────────────────────────────────────


def test_override_expiration():
    o = Override(
        axiom_id="Π.1.1",
        scope_type="FILE",
        scope_value="src/main.py",
        rationale="This is a very long rationale of more than twenty characters.",
        created_by="architect-1",
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
    )
    assert o.is_active is True
    assert isinstance(o.scope_type, ScopeType)


def test_override_permanent_requires_justification():
    """Permanent override without justification should raise."""
    with pytest.raises(ValidationError, match="permanent_justification"):
        Override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="f.py",
            rationale="A valid rationale for overriding this.",
            created_by="user",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
            is_permanent=True,
        )


def test_override_whitespace_justification_rejected():
    """Whitespace-only permanent justification should be rejected."""
    with pytest.raises(ValidationError, match="permanent_justification"):
        Override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="f.py",
            rationale="A valid rationale for overriding this.",
            created_by="user",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
            is_permanent=True,
            permanent_justification="   ",
        )


def test_override_permanent_valid_justification():
    """Permanent override with a valid SSO-PR- or SSO-SIG- prefix justification is accepted."""
    o = Override(
        axiom_id="Π.1.1",
        scope_type="FILE",
        scope_value="f.py",
        rationale="A valid rationale for overriding this.",
        created_by="user",
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
        is_permanent=True,
        permanent_justification="SSO-PR-12345-valid-substantive-justification",
    )
    assert o.is_permanent is True
    assert o.permanent_justification == "SSO-PR-12345-valid-substantive-justification"


def test_override_permanent_unprefixed_justification_rejected():
    """Permanent override with an unprefixed justification should raise ValidationError."""
    with pytest.raises(ValidationError, match="must start with either 'SSO-PR-' or 'SSO-SIG-'"):
        Override(
            axiom_id="Π.1.1",
            scope_type="FILE",
            scope_value="f.py",
            rationale="A valid rationale for overriding this.",
            created_by="user",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
            is_permanent=True,
            permanent_justification="This is an unprefixed but otherwise fine justification",
        )


# ── Attestation ────────────────────────────────────────────────────────


def test_attestation_confidence_range_valid():
    """Confidence within [0.0, 1.0] should be accepted."""
    a = Attestation(agent_id="a", task_id="t", confidence=0.85)
    assert a.confidence == 0.85
    assert a.status == AttestationStatus.PENDING


def test_attestation_confidence_too_high():
    """Confidence > 1.0 should be rejected."""
    with pytest.raises(ValidationError, match="less than or equal to 1"):
        Attestation(agent_id="a", task_id="t", confidence=1.5)


def test_attestation_confidence_too_low():
    """Confidence < 0.0 should be rejected."""
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        Attestation(agent_id="a", task_id="t", confidence=-0.1)


def test_attestation_confidence_boundary_values():
    """Boundary values 0.0 and 1.0 should be accepted."""
    a0 = Attestation(agent_id="a", task_id="t", confidence=0.0)
    assert a0.confidence == 0.0
    a1 = Attestation(agent_id="a", task_id="t", confidence=1.0)
    assert a1.confidence == 1.0
