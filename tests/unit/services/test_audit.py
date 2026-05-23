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
