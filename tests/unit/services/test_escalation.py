"""T042: Unit tests for escalation service.

Tests auto-routing of decisions based on criticality, 3-consecutive failure checks,
local retry queuing with exponential backoff, fail-closed agent blocking, and Human review rate tracking.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from ade_compliance.config import Config, GlobalSettings
from ade_compliance.models.decision import Decision
from ade_compliance.services.escalation import EscalationService, QueuedEscalation


@pytest.fixture
def config(tmp_path):
    db_file = tmp_path / f"audit_{uuid.uuid4().hex[:8]}.sqlite"
    # Ensure Windows paths are correctly formatted
    db_path = str(db_file).replace("\\", "/")
    return Config(global_settings=GlobalSettings(audit_path=db_path))


@pytest.fixture
def escalation_service(config):
    service = EscalationService(config)
    yield service
    service.audit.engine.dispose()
    service.engine.dispose()


class TestDecisionRouting:
    """Test Decision criticality routing and auto-approval (T043)."""

    @pytest.mark.asyncio
    async def test_evaluate_decision_auto_approves_low_medium(self, escalation_service):
        """Low/Medium criticality decisions should be auto-approved and return True."""
        decision_low = Decision(axiom_id="Π.1.1", rationale="Low risk", criticality="low")
        decision_med = Decision(axiom_id="Π.1.1", rationale="Med risk", criticality="medium")

        with patch.object(escalation_service, "escalate", new_callable=AsyncMock) as mock_escalate:
            res_low = await escalation_service.evaluate_decision(decision_low)
            res_med = await escalation_service.evaluate_decision(decision_med)

            assert res_low is True
            assert res_med is True
            mock_escalate.assert_not_called()

        # Verify audit trail logs the evaluation
        entries = escalation_service.audit.get_entries()
        actions = [e["action"] for e in entries]
        assert "DECISION_EVALUATED" in actions

    @pytest.mark.asyncio
    async def test_evaluate_decision_escalates_high_critical(self, escalation_service):
        """High/Critical decisions should require review, return False, and trigger escalation."""
        decision_high = Decision(axiom_id="Π.2.1", rationale="High risk", criticality="high")
        decision_crit = Decision(axiom_id="Π.2.1", rationale="Critical risk", criticality="critical")

        with patch.object(escalation_service, "escalate", new_callable=AsyncMock) as mock_escalate:
            mock_escalate.return_value = True

            res_high = await escalation_service.evaluate_decision(decision_high)
            res_crit = await escalation_service.evaluate_decision(decision_crit)

            assert res_high is False
            assert res_crit is False
            assert mock_escalate.call_count == 2


class TestEscalationQueuingAndBlocking:
    """Test local SQLite queue retries, backoff, and fail-closed blocking (T046)."""

    @pytest.mark.asyncio
    async def test_escalate_success_delivers(self, escalation_service):
        """Successful GitHub push should log ESCALATION_DELIVERED and return True."""
        with patch.object(escalation_service, "_push_to_github", new_callable=AsyncMock) as mock_push:
            mock_push.return_value = True

            success = await escalation_service.escalate("Test Title", "Test Body")
            assert success is True

            # Verify audit trail
            entries = escalation_service.audit.get_entries()
            assert any(e["action"] == "ESCALATION_DELIVERED" for e in entries)
            assert escalation_service.get_queue_depth() == 0

    @pytest.mark.asyncio
    async def test_escalate_failure_queues_locally(self, escalation_service):
        """Failed GitHub push should queue escalation locally with a future retry time."""
        with patch.object(escalation_service, "_push_to_github", new_callable=AsyncMock) as mock_push:
            mock_push.return_value = False

            success = await escalation_service.escalate("Test Title", "Test Body")
            assert success is False

            # Verify queue storage
            assert escalation_service.get_queue_depth() == 1
            entries = escalation_service.audit.get_entries()
            assert any(e["action"] == "ESCALATION_QUEUED" for e in entries)

            # Check next retry schedule
            session = escalation_service.Session()
            item = session.query(QueuedEscalation).first()
            assert item.title == "Test Title"
            assert item.retry_count == 0
            assert item.is_blocked is False
            assert item.next_retry > datetime.utcnow()
            session.close()

    @pytest.mark.asyncio
    async def test_process_queue_retries_and_backs_off(self, escalation_service):
        """Queue processor should retry and reschedule failed items using exponential backoff."""
        # Insert a queued escalation scheduled for retry now/past
        session = escalation_service.Session()
        entry = QueuedEscalation(
            title="Queued Title",
            body="Queued Body",
            retry_count=0,
            next_retry=datetime.utcnow() - timedelta(seconds=10)
        )
        session.add(entry)
        session.commit()
        session.close()

        # Run process_queue with failed GitHub push
        with patch.object(escalation_service, "_push_to_github", new_callable=AsyncMock) as mock_push:
            mock_push.return_value = False
            await escalation_service.process_queue()

        # Verify retry count incremented and next_retry rescheduled exponentially
        session = escalation_service.Session()
        item = session.query(QueuedEscalation).first()
        assert item.retry_count == 1
        # Backoff: 2^1 minutes = 2 minutes in future
        assert item.next_retry > datetime.utcnow() + timedelta(minutes=1)
        assert item.is_blocked is False
        session.close()

    @pytest.mark.asyncio
    async def test_process_queue_max_retries_exceeded_blocks_agent(self, escalation_service):
        """Exceeding max retries should block the escalation and block all subsequent agent actions (fail-closed)."""
        session = escalation_service.Session()
        entry = QueuedEscalation(
            title="Persistent Fail",
            body="Body content",
            retry_count=escalation_service.retry_max - 1, # Next failure reaches retry_max
            next_retry=datetime.utcnow() - timedelta(seconds=10)
        )
        session.add(entry)
        session.commit()
        session.close()

        assert escalation_service.is_agent_blocked() is False

        # Run process_queue with failed GitHub push
        with patch.object(escalation_service, "_push_to_github", new_callable=AsyncMock) as mock_push:
            mock_push.return_value = False
            await escalation_service.process_queue()

        # Verify escalation marked as blocked and agent blocked
        session = escalation_service.Session()
        item = session.query(QueuedEscalation).first()
        assert item.is_blocked is True
        assert item.error_message == "Max retries exceeded"
        session.close()

        assert escalation_service.is_agent_blocked() is True

        # Subsequent escalate calls must raise RuntimeError
        with pytest.raises(RuntimeError, match="Agent is blocked"):
            await escalation_service.escalate("New Title", "New Body")


class TestConsecutiveFailuresAndReviewRate:
    """Test 3-consecutive runs check and review rate calculations (T044, T047)."""

    def test_check_consecutive_failures(self, escalation_service):
        """Returns True if the last 3 completed runs all had violations."""
        # Clean state / no runs
        assert escalation_service.check_consecutive_failures() is False

        # 1. First failure
        escalation_service.audit.log("RUN_COMPLETE", {"violations_count": 2})
        assert escalation_service.check_consecutive_failures() is False

        # 2. Second failure
        escalation_service.audit.log("RUN_COMPLETE", {"violations_count": 1})
        assert escalation_service.check_consecutive_failures() is False

        # 3. Third failure -> consecutive failures should be True
        escalation_service.audit.log("RUN_COMPLETE", {"violations_count": 4})
        assert escalation_service.check_consecutive_failures() is True

        # 4. Success run clears consecutive failure pattern
        escalation_service.audit.log("RUN_COMPLETE", {"violations_count": 0})
        assert escalation_service.check_consecutive_failures() is False

    @pytest.mark.asyncio
    async def test_get_human_review_rate(self, escalation_service):
        """Should accurately calculate percentage of decisions requiring review."""
        assert escalation_service.get_human_review_rate() == 0.0

        # Create low/medium decisions (auto-approved)
        dec_1 = Decision(axiom_id="Π.1.1", rationale="OK", criticality="low")
        dec_2 = Decision(axiom_id="Π.1.2", rationale="OK", criticality="medium")
        
        # Create high decision (requires human review)
        dec_3 = Decision(axiom_id="Π.1.3", rationale="Review", criticality="high")

        with patch.object(escalation_service, "escalate", new_callable=AsyncMock) as mock_escalate:
            mock_escalate.return_value = True

            await escalation_service.evaluate_decision(dec_1)
            await escalation_service.evaluate_decision(dec_2)
            await escalation_service.evaluate_decision(dec_3)

        # 1 out of 3 decisions requires human review -> 33.3%
        rate = escalation_service.get_human_review_rate()
        assert pytest.approx(rate, 0.01) == 0.333
