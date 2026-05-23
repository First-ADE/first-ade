"""T061: Attestation service for agent self-governance.

Provides pre-execution compliance self-checks and post-task attestation
recording with confidence-based escalation (confidence < 0.7 triggers escalation).
"""

from typing import List

from ..config import Config
from ..models.axiom import Violation
from ..models.decision import Attestation
from ..models.report import ComplianceReport
from ..services.audit import AuditService

CONFIDENCE_THRESHOLD = 0.7


class AttestationService:
    """Service for recording agent attestations and running pre-execution checks."""

    def __init__(self, config: Config):
        self.config = config
        self.audit = AuditService(config)

    def record(
        self,
        agent_id: str,
        task_id: str,
        confidence: float,
        axioms_applied: List[str] | None = None,
    ) -> Attestation:
        """Record an attestation. Escalates if confidence < threshold.

        Args:
            agent_id: Identifier for the agent making the attestation.
            task_id: Identifier for the task being attested.
            confidence: Agent's confidence score (0.0 to 1.0).
            axioms_applied: List of axiom IDs that were applied.

        Returns:
            The recorded Attestation with status set to 'passed' or 'escalated'.
        """
        if axioms_applied is None:
            axioms_applied = []

        # Determine status based on confidence threshold
        if confidence < CONFIDENCE_THRESHOLD:
            status = "escalated"
        else:
            status = "passed"

        attestation = Attestation(
            agent_id=agent_id,
            task_id=task_id,
            confidence=confidence,
            axioms_applied=axioms_applied,
            status=status,
        )

        # Log to audit trail
        self.audit.log(
            "ATTESTATION_RECORDED",
            {
                "agent_id": agent_id,
                "task_id": task_id,
                "confidence": confidence,
                "axioms_applied": axioms_applied,
                "status": status,
            },
        )

        # Safe async runner helper
        def run_async_safe(coro):
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(lambda: asyncio.run(coro))
                    return future.result()
            else:
                return asyncio.run(coro)

        # If escalated, log escalation event and trigger EscalationService
        from ..models.decision import Decision
        from ..services.escalation import EscalationService
        
        escalation_service = EscalationService(self.config)

        if status == "escalated":
            self.audit.log(
                "ESCALATION_TRIGGERED",
                {
                    "agent_id": agent_id,
                    "task_id": task_id,
                    "confidence": confidence,
                    "reason": f"Confidence {confidence} below threshold {CONFIDENCE_THRESHOLD}",
                },
            )
            title = f"[ADE Escalation] Low-Confidence Attestation: Task {task_id}"
            body = (
                f"Agent attestation has low confidence and was escalated.\n\n"
                f"- **Agent ID**: {agent_id}\n"
                f"- **Task ID**: {task_id}\n"
                f"- **Confidence**: {confidence}\n"
                f"- **Axioms Applied**: {', '.join(axioms_applied)}\n"
            )
            try:
                run_async_safe(escalation_service.escalate(title, body))
            except Exception:
                # Do not block if escalation is queued/blocked, or let it raise if blocked
                if escalation_service.is_agent_blocked():
                    raise

        # Evaluate decision criticality for each applied axiom
        for axiom_id in axioms_applied:
            criticality = "medium"
            if "critical" in axiom_id or axiom_id.startswith("Π.5"):
                criticality = "critical"
            elif "high" in axiom_id:
                criticality = "high"

            decision = Decision(
                axiom_id=axiom_id,
                rationale=f"Agent attested {axiom_id} during task {task_id}",
                criticality=criticality,
            )
            try:
                run_async_safe(escalation_service.evaluate_decision(decision))
            except Exception:
                if escalation_service.is_agent_blocked():
                    raise

        return attestation

    async def pre_check(self, files: List[str]) -> List[Violation]:
        """Run pre-execution compliance self-check on specified files.

        Args:
            files: List of file paths to check.

        Returns:
            List of violations found.
        """
        self.audit.log("PRE_CHECK_RUN", {"files_count": len(files)})

        report = await self._run_orchestrator(files)
        return report.violations

    async def _run_orchestrator(self, files: List[str]) -> ComplianceReport:
        """Run the orchestrator on the given files.

        This is separated out so it can be mocked in tests.
        """
        from ..services.orchestrator import Orchestrator

        orchestrator = Orchestrator(self.config)
        return await orchestrator.run(files)
