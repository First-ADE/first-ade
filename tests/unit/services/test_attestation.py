"""T059: Unit tests for attestation service.

Tests attestation recording, confidence threshold escalation,
and pre-execution compliance checks.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from ade_compliance.config import Config, GlobalSettings
from ade_compliance.models.axiom import Violation, ViolationState
from ade_compliance.models.decision import Attestation
from ade_compliance.models.report import ComplianceReport
from ade_compliance.services.attestation import AttestationService


@pytest.fixture
def config(tmp_path):
    db_file = tmp_path / f"audit_{uuid.uuid4().hex[:8]}.sqlite"
    return Config(global_settings=GlobalSettings(audit_path=str(db_file).replace("\\", "/")))


@pytest.fixture
def attestation_service(config):
    service = AttestationService(config)
    yield service
    service.audit.engine.dispose()


class TestRecordAttestation:
    """Test attestation recording with various confidence levels."""

    def test_record_high_confidence_passes(self, attestation_service):
        """Attestation with confidence >= 0.7 should be recorded as passed."""
        result = attestation_service.record(
            agent_id="agent-1",
            task_id="T001",
            confidence=0.9,
            axioms_applied=["S.1", "S.2"],
        )

        assert isinstance(result, Attestation)
        assert result.agent_id == "agent-1"
        assert result.task_id == "T001"
        assert result.confidence == 0.9
        assert result.axioms_applied == ["S.1", "S.2"]
        assert result.status == "passed"

    def test_record_exact_threshold_passes(self, attestation_service):
        """Attestation at exactly 0.7 confidence should pass (threshold is strictly less-than)."""
        result = attestation_service.record(
            agent_id="agent-1",
            task_id="T002",
            confidence=0.7,
            axioms_applied=["S.1"],
        )
        assert result.status == "passed"

    def test_record_low_confidence_escalates(self, attestation_service):
        """Attestation with confidence < 0.7 should be escalated."""
        result = attestation_service.record(
            agent_id="agent-1",
            task_id="T003",
            confidence=0.5,
            axioms_applied=["S.1"],
        )
        assert result.status == "escalated"

    def test_record_zero_confidence_escalates(self, attestation_service):
        """Attestation with zero confidence should be escalated."""
        result = attestation_service.record(
            agent_id="agent-1",
            task_id="T004",
            confidence=0.0,
            axioms_applied=[],
        )
        assert result.status == "escalated"

    def test_record_logs_to_audit(self, attestation_service):
        """Every attestation should be logged to the audit trail."""
        attestation_service.record(
            agent_id="agent-1",
            task_id="T005",
            confidence=0.9,
            axioms_applied=["S.1"],
        )

        entries = attestation_service.audit.get_entries()
        assert len(entries) >= 1
        assert entries[0]["action"] == "ATTESTATION_RECORDED"
        assert entries[0]["details"]["agent_id"] == "agent-1"
        assert entries[0]["details"]["status"] == "passed"

    def test_escalation_logs_escalation_entry(self, attestation_service):
        """Low-confidence attestation should log an additional ESCALATION_TRIGGERED entry."""
        attestation_service.record(
            agent_id="agent-1",
            task_id="T006",
            confidence=0.3,
            axioms_applied=["S.1"],
        )

        entries = attestation_service.audit.get_entries()
        actions = [e["action"] for e in entries]
        assert "ESCALATION_TRIGGERED" in actions
        assert "ATTESTATION_RECORDED" in actions


class TestPreCheck:
    """Test pre-execution compliance self-checks."""

    @pytest.mark.asyncio
    async def test_pre_check_compliant_files(self, attestation_service):
        """Pre-check on compliant files should return empty violations."""
        mock_report = ComplianceReport(repo_root=".", violations=[])

        with patch.object(attestation_service, "_run_orchestrator", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_report
            violations = await attestation_service.pre_check(["src/good_file.py"])

        assert violations == []

    @pytest.mark.asyncio
    async def test_pre_check_non_compliant_files(self, attestation_service):
        """Pre-check on non-compliant files should return violations."""
        test_violations = [Violation(axiom_id="S.1", file_path="bad.py", message="No spec", state=ViolationState.NEW)]
        mock_report = ComplianceReport(repo_root=".", violations=test_violations)

        with patch.object(attestation_service, "_run_orchestrator", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_report
            violations = await attestation_service.pre_check(["bad.py"])

        assert len(violations) == 1
        assert violations[0].axiom_id == "S.1"

    @pytest.mark.asyncio
    async def test_pre_check_logs_to_audit(self, attestation_service):
        """Pre-check should log the check to the audit trail."""
        mock_report = ComplianceReport(repo_root=".", violations=[])

        with patch.object(attestation_service, "_run_orchestrator", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_report
            await attestation_service.pre_check(["src/file.py"])

        entries = attestation_service.audit.get_entries()
        assert any(e["action"] == "PRE_CHECK_RUN" for e in entries)
