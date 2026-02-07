import pytest
import json
import tempfile
import os
from ade_compliance.services.audit import AuditService
from ade_compliance.config import Config, GlobalSettings

@pytest.fixture
def audit_service():
    config = Config()
    config.global_settings.audit_path = ":memory:"
    return AuditService(config)

def test_audit_log_single_entry(audit_service):
    """Verify that a single entry is logged correctly."""
    audit_service.log("CHECK_RUN", {"files": 5, "engine": "spec"})
    entries = audit_service.get_entries()
    assert len(entries) == 1
    assert entries[0]["action"] == "CHECK_RUN"
    assert entries[0]["details"]["files"] == 5

def test_audit_log_multiple_entries(audit_service):
    """Verify multiple entries are logged in order."""
    audit_service.log("CHECK_START", {"files": 3})
    audit_service.log("CHECK_COMPLETE", {"violations": 2})
    audit_service.log("REPORT_GENERATED", {"format": "json"})
    entries = audit_service.get_entries()
    assert len(entries) == 3
    # Most recent first
    assert entries[0]["action"] == "REPORT_GENERATED"
    assert entries[2]["action"] == "CHECK_START"

def test_audit_hash_chain(audit_service):
    """Verify that entries have hashes."""
    audit_service.log("ACTION_1", {"data": "first"})
    audit_service.log("ACTION_2", {"data": "second"})
    entries = audit_service.get_entries()
    assert len(entries) == 2
    for entry in entries:
        assert "hash" in entry
        assert len(entry["hash"]) == 64  # SHA-256

def test_audit_entry_has_timestamp(audit_service):
    """Verify entries have timestamps."""
    audit_service.log("TEST_ACTION", {"key": "value"})
    entries = audit_service.get_entries()
    assert entries[0]["timestamp"] is not None

def test_audit_get_entries_limit(audit_service):
    """Verify entries can be limited."""
    for i in range(10):
        audit_service.log(f"ACTION_{i}", {"index": i})
    entries = audit_service.get_entries(limit=5)
    assert len(entries) == 5

def test_audit_get_entries_empty(audit_service):
    """Verify empty audit log returns empty list."""
    entries = audit_service.get_entries()
    assert entries == []
