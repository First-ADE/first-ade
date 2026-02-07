from ade_compliance.models.axiom import Axiom, Violation, ViolationState, TraceLink
from ade_compliance.models.decision import Decision, Override

def test_axiom_creation():
    axiom = Axiom(id="Π.1.1", name="Spec Governance", category="SPECIFICATION", severity="high")
    assert axiom.id == "Π.1.1"
    assert axiom.enabled is True

def test_violation_state_machine():
    v = Violation(axiom_id="Π.1.1", file_path="src/main.py", message="No spec")
    assert v.state == ViolationState.NEW
    
    v.acknowledge()
    assert v.state == ViolationState.ACKNOWLEDGED
    
    v.resolve()
    assert v.state == ViolationState.RESOLVED

def test_tracelink_matrix():
    link = TraceLink(source="src/main.py", target="tests/test_main.py", type="validates")
    assert link.source == "src/main.py"

def test_decision_criticality():
    d = Decision(axiom_id="Π.5.3", rationale="Test", criticality="critical")
    assert d.requires_human_review is True

def test_override_expiration():
    o = Override(axiom_id="Π.1.1", rationale="Emergency", criticality="medium", expires_in_days=1)
    assert o.is_active is True
    # Testing time-dependent logic would require mocking/freezing time
