from unittest.mock import patch

from ade_compliance.config import Config, get_axiom_strictness
from ade_compliance.services.override import OverrideService


def test_get_axiom_strictness_cascading():
    """Verify that get_axiom_strictness cascades correctly from axiom -> engine -> global."""
    cfg = Config()
    cfg.global_settings.strictness = "audit"
    cfg.engines.spec.strictness = "warn"
    cfg.axioms = {"Π.1.1": "enforce"}

    # 1. Axiom specific level is found first
    assert get_axiom_strictness(cfg, "Π.1.1") == "enforce"

    # 2. Axiom is not configured -> falls back to spec engine
    assert get_axiom_strictness(cfg, "Π.1.2") == "warn"

    # 3. Axiom starts with something else -> falls back to global
    assert get_axiom_strictness(cfg, "Π.9.9") == "audit"


def test_override_service_expiring_notifications(tmp_path):
    """Verify that active overrides expiring in <= 7 days trigger an alert, and are flagged so no duplicate alert is sent."""
    db_file = str(tmp_path / "test_expiring_audit.sqlite").replace("\\", "/")
    cfg = Config()
    cfg.global_settings.audit_path = db_file

    svc = OverrideService(cfg)

    # 1. Create a non-permanent override expiring in 5 days (expires_in_days=5)
    # Wait, the create_override method calculates expires_at based on expires_in_days.
    # To test expiring in <= 7 days, we can pass expires_in_days=5
    # Rationale must be at least 20 chars
    o = svc.create_override(
        axiom_id="Π.1.1",
        scope_type="FILE",
        scope_value="src/main.py",
        rationale="My long justification rationale for override test.",
        created_by="architect-1",
        expires_in_days=5,
    )

    # 2. Create another permanent override (should not trigger alert)
    o_perm = svc.create_override(
        axiom_id="Π.2.1",
        scope_type="FILE",
        scope_value="src/test.py",
        rationale="My long justification rationale for override test.",
        created_by="architect-1",
        is_permanent=True,
        permanent_justification="Permanent necessity because of system constraints.",
    )

    # 3. Create another override expiring in 30 days (should not trigger alert)
    o_far = svc.create_override(
        axiom_id="Π.3.1",
        scope_type="FILE",
        scope_value="src/trace.py",
        rationale="My long justification rationale for override test.",
        created_by="architect-1",
        expires_in_days=30,
    )

    # Mock the EscalationService's escalate method
    with patch("ade_compliance.services.escalation.EscalationService.escalate") as mock_escalate:
        # Check expiring overrides
        expiring = svc.check_expiring_overrides()

        # Only the 5-day expiring one should be detected and notified
        assert len(expiring) == 1
        assert expiring[0].axiom_id == "Π.1.1"
        mock_escalate.assert_called_once()

        # Verify that running it a second time does not notify again (due to SQLite flag update)
        mock_escalate.reset_mock()
        expiring_second = svc.check_expiring_overrides()
        assert len(expiring_second) == 0
        mock_escalate.assert_not_called()
