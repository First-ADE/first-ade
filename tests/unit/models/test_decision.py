# implements: FR-008
# traces_to: P.2.1

"""Unit tests for decision, override, and attestation models."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from ade_compliance.models.decision import (
    Attestation,
    AttestationStatus,
    Criticality,
    Decision,
    Override,
    ScopeType,
)


def test_decision_criticality():
    d = Decision(axiom_id="P.5.3", rationale="Test", criticality="critical")
    assert d.requires_human_review is True
    assert isinstance(d.criticality, Criticality)


def test_decision_low_criticality_auto_approved():
    """Low/medium criticality should NOT require human review."""
    d = Decision(axiom_id="P.1.1", rationale="Test", criticality="low")
    assert d.requires_human_review is False


def test_override_expiration():
    o = Override(
        axiom_id="P.1.1",
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
            axiom_id="P.1.1",
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
            axiom_id="P.1.1",
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
        axiom_id="P.1.1",
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
            axiom_id="P.1.1",
            scope_type="FILE",
            scope_value="f.py",
            rationale="A valid rationale for overriding this.",
            created_by="user",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1),
            is_permanent=True,
            permanent_justification="This is an unprefixed but otherwise fine justification",
        )


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
