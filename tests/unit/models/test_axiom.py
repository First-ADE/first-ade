# implements: FR-007
# traces_to: P.2.1

"""Unit tests for axiom and violation models."""

import pytest

from ade_compliance.models.axiom import (
    Axiom,
    InvalidStateTransition,
    Severity,
    TraceLink,
    Violation,
    ViolationState,
)


def test_axiom_creation():
    axiom = Axiom(id="P.1.1", name="Spec Governance", category="SPECIFICATION", severity="high")
    assert axiom.id == "P.1.1"
    assert axiom.enabled is True


def test_violation_state_machine():
    v = Violation(axiom_id="P.1.1", file_path="src/main.py", message="No spec")
    assert v.state == ViolationState.NEW
    assert v.resolved_at is None

    v.acknowledge()
    assert v.state == ViolationState.ACKNOWLEDGED

    v.resolve()
    assert v.state == ViolationState.RESOLVED
    assert v.resolved_at is not None


def test_violation_cannot_resolve_from_new():
    """Resolving directly from NEW is not allowed (must acknowledge first)."""
    v = Violation(axiom_id="P.1.1", file_path="src/main.py", message="No spec")
    with pytest.raises(InvalidStateTransition, match="must be 'acknowledged'"):
        v.resolve()


def test_violation_cannot_acknowledge_from_resolved():
    """RESOLVED is terminal - no backward transitions."""
    v = Violation(axiom_id="P.1.1", file_path="src/main.py", message="No spec")
    v.acknowledge()
    v.resolve()
    with pytest.raises(InvalidStateTransition, match="must be 'new'"):
        v.acknowledge()


def test_violation_override_from_new():
    """Override should work from NEW state."""
    v = Violation(axiom_id="P.1.1", file_path="src/main.py", message="No spec")
    v.override()
    assert v.state == ViolationState.OVERRIDDEN
    assert v.resolved_at is not None


def test_violation_override_from_acknowledged():
    """Override should work from ACKNOWLEDGED state."""
    v = Violation(axiom_id="P.1.1", file_path="src/main.py", message="No spec")
    v.acknowledge()
    v.override()
    assert v.state == ViolationState.OVERRIDDEN


def test_violation_cannot_override_from_resolved():
    """Cannot override from RESOLVED (terminal state)."""
    v = Violation(axiom_id="P.1.1", file_path="src/main.py", message="No spec")
    v.acknowledge()
    v.resolve()
    with pytest.raises(InvalidStateTransition, match="terminal state"):
        v.override()


def test_violation_cannot_override_twice():
    """Cannot override from OVERRIDDEN (terminal state)."""
    v = Violation(axiom_id="P.1.1", file_path="src/main.py", message="No spec")
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


def test_tracelink_matrix():
    link = TraceLink(source="src/main.py", target="tests/test_main.py", type="validates")
    assert link.source == "src/main.py"
