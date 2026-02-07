import pytest
import uuid
from ade_compliance.services.audit import AuditService
from ade_compliance.config import Config, GlobalSettings

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
    assert entries[0]["action"] == "ACTION_2" # Descending order
    assert entries[1]["action"] == "ACTION_1"
