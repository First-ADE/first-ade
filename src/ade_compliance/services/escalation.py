# implements: FR-009
# traces_to: Π.5.3

"""T043/T044/T045/T046/T047: Escalation service for routing critical decisions to Human Architect.

Provides:
- Decision criticality classification and auto-routing.
- Consecutive failure detection.
- Local SQLite queue with exponential backoff retries.
- GitHub API integration for issue creation.
- Human Architect review rate tracking.
Consolidates engine setup using the centralized database manager.
"""

import json
import os
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import Boolean, Column, DateTime, Integer, String

from ..config import Config
from ..models.decision import Decision
from ..observability.metrics import escalation_queue_depth, escalation_total
from ..services.audit import AuditEntry, AuditService
from .db import Base, db_session


class QueuedEscalation(Base):
    __tablename__ = "escalation_queue"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    retry_count = Column(Integer, default=0)
    next_retry = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_blocked = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)


class EscalationService:
    def __init__(self, config: Config):
        self.config = config
        self.audit = AuditService(config)

        from sqlalchemy.orm import sessionmaker

        from .db import Base as db_Base
        from .db import get_engine

        self.engine = get_engine(config)
        db_Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

        # GitHub configuration from config
        self.github_repo = self.config.escalation.github_repo
        self.retry_max = self.config.escalation.retry_max
        self.backoff_factor = 2  # base for exponential backoff (2^retry_count minutes)

        self._update_queue_metric()

    def _update_queue_metric(self):
        """Update the Prometheus gauge for queue depth."""
        try:
            escalation_queue_depth.set(self.get_queue_depth())
        except Exception:
            pass

    def get_queue_depth(self) -> int:
        """Get number of active (non-blocked) items in local queue."""
        with db_session(self.config) as session:
            return session.query(QueuedEscalation).filter(QueuedEscalation.is_blocked == False).count()

    def is_agent_blocked(self) -> bool:
        """Check if agent is blocked due to undelivered/blocked queue items (fail-closed)."""
        with db_session(self.config) as session:
            blocked_count = session.query(QueuedEscalation).filter(QueuedEscalation.is_blocked == True).count()
            return blocked_count > 0

    async def evaluate_decision(self, decision: Decision) -> bool:
        """Evaluate decision. Routes high/critical to Human Architect."""
        # Log decision evaluation
        self.audit.log(
            "DECISION_EVALUATED",
            {
                "axiom_id": decision.axiom_id,
                "criticality": decision.criticality,
                "requires_human_review": decision.requires_human_review,
                "rationale": decision.rationale,
            },
        )

        if decision.requires_human_review:
            title = f"[ADE Escalation] Critical Decision Required: {decision.axiom_id}"
            body = (
                f"A compliance decision requires Human Architect review (criticality: {decision.criticality}).\n\n"
                f"- **Axiom ID**: {decision.axiom_id}\n"
                f"- **Rationale**: {decision.rationale}\n"
                f"- **Timestamp**: {decision.timestamp.isoformat()}\n"
            )
            await self.escalate(title, body)
            return False

        return True

    async def escalate(self, title: str, body: str) -> bool:
        """Escalate a notification. Attempts to post to GitHub, otherwise queues locally."""
        if self.is_agent_blocked():
            raise RuntimeError("Agent is blocked due to undelivered escalations in the local queue (fail-closed).")

        escalation_total.inc()

        success = await self._push_to_github(title, body)
        if success:
            self.audit.log("ESCALATION_DELIVERED", {"title": title})
            return True

        # Queue locally
        with db_session(self.config) as session:
            next_retry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
                minutes=1
            )  # first retry in 1 minute
            entry = QueuedEscalation(
                title=title,
                body=body,
                retry_count=0,
                next_retry=next_retry,
            )
            session.add(entry)

        self.audit.log("ESCALATION_QUEUED", {"title": title})
        self._update_queue_metric()
        return False

    def check_consecutive_failures(self) -> bool:
        """Check if the last 3 consecutive runs finished with violations (failure)."""
        with db_session(self.config) as session:
            # Query last 3 RUN_COMPLETE actions
            runs = (
                session.query(AuditEntry)
                .filter(AuditEntry.action == "RUN_COMPLETE")
                .order_by(AuditEntry.id.desc())
                .limit(3)
                .all()
            )
            if len(runs) < 3:
                return False

            for run in runs:
                try:
                    details = json.loads(run.details)
                    if details.get("violations_count", 0) == 0:
                        return False
                except Exception:
                    return False
            return True

    async def process_queue(self) -> None:
        """Process any pending local queued escalations with exponential backoff."""
        with db_session(self.config) as session:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            pending = (
                session.query(QueuedEscalation)
                .filter(QueuedEscalation.is_blocked == False, QueuedEscalation.next_retry <= now)
                .all()
            )

            for item in pending:
                success = await self._push_to_github(item.title, item.body)
                if success:
                    session.delete(item)
                    self.audit.log("ESCALATION_DELIVERED_FROM_QUEUE", {"id": item.id, "title": item.title})
                else:
                    item.retry_count += 1
                    if item.retry_count >= self.retry_max:
                        item.is_blocked = True
                        item.error_message = "Max retries exceeded"
                        self.audit.log(
                            "ESCALATION_BLOCKED", {"id": item.id, "title": item.title, "error": "Max retries exceeded"}
                        )
                    else:
                        minutes = self.backoff_factor**item.retry_count
                        item.next_retry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=minutes)
                        self.audit.log(
                            "ESCALATION_RETRY_SCHEDULED",
                            {
                                "id": item.id,
                                "title": item.title,
                                "retry_count": item.retry_count,
                                "next_retry": item.next_retry.isoformat(),
                            },
                        )

        self._update_queue_metric()

    def get_human_review_rate(self) -> float:
        """Calculate the percentage of all compliance decisions requiring human review."""
        with db_session(self.config) as session:
            entries = session.query(AuditEntry).filter(AuditEntry.action == "DECISION_EVALUATED").all()
            if not entries:
                return 0.0

            total = len(entries)
            human_reviews = 0
            for e in entries:
                try:
                    details = json.loads(e.details)
                    if details.get("requires_human_review", False):
                        human_reviews += 1
                except Exception:
                    pass

            return human_reviews / total

    async def _push_to_github(self, title: str, body: str) -> bool:
        """Call the GitHub API to create an issue for the escalation."""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return False

        owner, repo = self.github_repo.split("/", 1)
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ADE-Compliance-Agent",
        }
        payload = {
            "title": title,
            "body": body,
            "labels": ["ade-escalation", "priority:critical"],
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)
                return response.status_code == 201
        except Exception:
            return False
