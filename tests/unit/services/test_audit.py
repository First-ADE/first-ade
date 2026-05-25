import uuid

import pytest

from ade_compliance.config import Config, GlobalSettings
from ade_compliance.services.audit import AuditService


@pytest.fixture
def audit_service(tmp_path):
    # Use unique file per test for guaranteed isolation
    db_file = tmp_path / f"audit_{uuid.uuid4().hex[:8]}.sqlite"
    config = Config(global_settings=GlobalSettings(audit_path=str(db_file).replace("\\", "/")))
    service = AuditService(config)
    # Force clean state
    with service.engine.connect() as conn:
        from sqlalchemy import text

        conn.execute(text("DELETE FROM audit_log"))
        conn.commit()
    yield service
    service.engine.dispose()


def test_audit_logging(audit_service):
    audit_service.log("TEST_ACTION", {"user": "agent"})
    entries = audit_service.get_entries()
    assert len(entries) == 1
    assert entries[0]["action"] == "TEST_ACTION"
    assert entries[0]["details"]["user"] == "agent"


def test_hash_chain_integrity(audit_service):
    audit_service.log("ACTION_1", {})
    audit_service.log("ACTION_2", {})

    # We can't verify hash internally easily without exposing model, but we verify we can read back 2 entries
    entries = audit_service.get_entries(limit=2)
    assert len(entries) == 2
    assert entries[0]["action"] == "ACTION_2"  # Descending order
    assert entries[1]["action"] == "ACTION_1"


def test_verify_chain_success(audit_service):
    audit_service.log("ACTION_1", {"key": "val1"})
    audit_service.log("ACTION_2", {"key": "val2"})
    success, errors = audit_service.verify_chain()
    assert success is True
    assert len(errors) == 0


def test_verify_chain_tampered_details(audit_service):
    audit_service.log("ACTION_1", {"key": "val1"})
    audit_service.log("ACTION_2", {"key": "val2"})

    # Tamper with the details of ACTION_1 directly in the database
    from sqlalchemy import text

    with audit_service.engine.connect() as conn:
        conn.execute(text("UPDATE audit_log SET details = '{\"key\": \"tampered\"}' WHERE action = 'ACTION_1'"))
        conn.commit()

    success, errors = audit_service.verify_chain()
    assert success is False
    assert len(errors) > 0
    assert any("hash" in err.lower() or "broken" in err.lower() for err in errors)


def test_verify_chain_tampered_previous_hash(audit_service):
    audit_service.log("ACTION_1", {"key": "val1"})
    audit_service.log("ACTION_2", {"key": "val2"})

    # Tamper with the previous_hash of ACTION_2 directly in the database
    from sqlalchemy import text

    with audit_service.engine.connect() as conn:
        conn.execute(text("UPDATE audit_log SET previous_hash = 'invalid_hash_value' WHERE action = 'ACTION_2'"))
        conn.commit()

    success, errors = audit_service.verify_chain()
    assert success is False
    assert len(errors) > 0


def test_get_trend_report_empty(audit_service):
    """T049: Test trend report returns zeros when no entries exist."""
    report = audit_service.get_trend_report(days=30)

    assert report["days"] == 30
    assert report["runs_count"] == 0
    assert report["violations_count"] == 0
    assert report["violations_by_day"] == {}
    assert report["violations_by_axiom"] == {}
    assert report["violations_by_severity"] == {}
    assert report["overrides_count"] == 0
    assert report["overrides_by_day"] == {}


def test_get_trend_report_with_run_data(audit_service):
    """T049: Log RUN_COMPLETE and VIOLATION_DETECTED events, verify trend report counts."""
    audit_service.log("RUN_COMPLETE", {"violations_count": 3})
    audit_service.log("RUN_COMPLETE", {"violations_count": 2})
    audit_service.log("VIOLATION_DETECTED", {"axiom_id": "Π.1.1", "severity": "high"})
    audit_service.log("VIOLATION_DETECTED", {"axiom_id": "Π.1.1", "severity": "high"})
    audit_service.log("VIOLATION_DETECTED", {"axiom_id": "Π.2.1", "severity": "medium"})

    report = audit_service.get_trend_report(days=30)

    assert report["runs_count"] == 2
    assert report["violations_count"] == 5  # 3 + 2 from RUN_COMPLETE
    assert report["violations_by_axiom"]["Π.1.1"] == 2
    assert report["violations_by_axiom"]["Π.2.1"] == 1
    assert report["violations_by_severity"]["high"] == 2
    assert report["violations_by_severity"]["medium"] == 1


def test_get_trend_report_with_overrides(audit_service):
    """T050: Log OVERRIDE_RECORDED events, verify overrides_count and overrides_by_day."""
    from datetime import datetime, timezone

    audit_service.log("OVERRIDE_RECORDED", {"override_id": "o1", "axiom_id": "Π.1.1"})
    audit_service.log("OVERRIDE_RECORDED", {"override_id": "o2", "axiom_id": "Π.2.1"})
    audit_service.log("OVERRIDE_RECORDED", {"override_id": "o3", "axiom_id": "Π.1.1"})

    report = audit_service.get_trend_report(days=30)

    assert report["overrides_count"] == 3
    # All overrides logged today, so overrides_by_day should have one key
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert today in report["overrides_by_day"]
    assert report["overrides_by_day"][today] == 3


def test_get_entries_returns_recent(audit_service):
    """T050: Verify get_entries returns entries in descending order with correct limit."""
    for i in range(5):
        audit_service.log(f"ACTION_{i}", {"index": i})

    # Get all entries
    all_entries = audit_service.get_entries(limit=100)
    assert len(all_entries) == 5
    # Verify descending order (most recent first)
    assert all_entries[0]["action"] == "ACTION_4"
    assert all_entries[4]["action"] == "ACTION_0"

    # Verify limit works
    limited = audit_service.get_entries(limit=2)
    assert len(limited) == 2
    assert limited[0]["action"] == "ACTION_4"
    assert limited[1]["action"] == "ACTION_3"
