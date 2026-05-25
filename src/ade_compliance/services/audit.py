# implements: FR-007
# traces_to: Π.3.1

"""T041: Tamper-proof append-only audit trail logic for compliance events.

Logs framework runs, violations, and override registrations with SHA-256 validation.
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import Column, DateTime, Integer, String

from ..config import Config
from ..exceptions import DatabaseException
from ..observability.logging import logger
from .base import BaseService
from .db import Base


class AuditEntry(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    action = Column(String)
    details = Column(String)  # JSON
    previous_hash = Column(String)
    hash = Column(String)


class AuditService(BaseService):
    """Service to record and verify tamper-proof append-only audit logs."""

    def __init__(self, config: Config):
        super().__init__(config)
        # Ensure database is initialized and expose engine/sessionmaker for backward compatibility
        self.engine = self.db_manager.get_engine(self.config)
        _, session_factory = self.db_manager.get_engine_and_factory(self.config)
        self.Session = session_factory

    def log(self, action: str, details: Dict[str, Any]) -> None:
        """Append a new cryptographic entry to the audit log."""
        # Log structured JSON to stdout using loguru
        logger.info("audit_event", action=action, details=details)

        try:
            with self.db_manager.session(self.config) as session:
                # Query last hash for cryptographic chain
                last_entry = session.query(AuditEntry).order_by(AuditEntry.id.desc()).first()
                prev_hash = last_entry.hash if last_entry else "0" * 64

                # Serialize details
                details_json = json.dumps(details, sort_keys=True)

                # Calculate new hash
                timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
                payload = f"{timestamp.isoformat()}{action}{details_json}{prev_hash}"
                entry_hash = hashlib.sha256(payload.encode()).hexdigest()

                entry = AuditEntry(
                    timestamp=timestamp, action=action, details=details_json, previous_hash=prev_hash, hash=entry_hash
                )
                session.add(entry)
        except Exception as e:
            if isinstance(e, DatabaseException):
                raise
            raise DatabaseException(f"Failed to write audit entry for action '{action}': {e}") from e

    def get_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent audit log entries."""
        try:
            with self.db_manager.session(self.config) as session:
                entries = session.query(AuditEntry).order_by(AuditEntry.id.desc()).limit(limit).all()
                return [
                    {
                        "timestamp": e.timestamp.isoformat(),
                        "action": e.action,
                        "details": json.loads(e.details),
                        "hash": e.hash,
                    }
                    for e in entries
                ]
        except Exception as e:
            if isinstance(e, DatabaseException):
                raise
            raise DatabaseException(f"Failed to fetch audit log entries: {e}") from e

    def get_trend_report(self, days: int = 30) -> Dict[str, Any]:
        """Aggregate compliance metrics and trends over the last specified number of days."""
        try:
            with self.db_manager.session(self.config) as session:
                cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
                entries = session.query(AuditEntry).filter(AuditEntry.timestamp >= cutoff).all()

                runs_count = 0
                violations_count = 0
                violations_by_day = {}
                violations_by_axiom = {}
                violations_by_severity = {}
                overrides_count = 0
                overrides_by_day = {}

                for e in entries:
                    date_str = e.timestamp.strftime("%Y-%m-%d")
                    details = {}
                    try:
                        details = json.loads(e.details)
                    except (json.JSONDecodeError, TypeError) as err:
                        logger.warning(
                            f"Failed to parse audit log details for entry ID {e.id} "
                            f"(action: '{e.action}', timestamp: {e.timestamp.isoformat()}): {err}"
                        )

                    if e.action == "RUN_COMPLETE":
                        runs_count += 1
                        v_count = details.get("violations_count", 0)
                        violations_count += v_count
                        violations_by_day[date_str] = violations_by_day.get(date_str, 0) + v_count

                    elif e.action == "PRE_CHECK_RUN":
                        runs_count += 1

                    elif e.action == "VIOLATION_DETECTED":
                        ax = details.get("axiom_id", "unknown")
                        sev = details.get("severity", "unknown")
                        violations_by_axiom[ax] = violations_by_axiom.get(ax, 0) + 1
                        violations_by_severity[sev] = violations_by_severity.get(sev, 0) + 1

                    elif e.action == "OVERRIDE_RECORDED":
                        overrides_count += 1
                        overrides_by_day[date_str] = overrides_by_day.get(date_str, 0) + 1

                return {
                    "days": days,
                    "runs_count": runs_count,
                    "violations_count": violations_count,
                    "violations_by_day": violations_by_day,
                    "violations_by_axiom": violations_by_axiom,
                    "violations_by_severity": violations_by_severity,
                    "overrides_count": overrides_count,
                    "overrides_by_day": overrides_by_day,
                }
        except Exception as e:
            if isinstance(e, DatabaseException):
                raise
            raise DatabaseException(f"Failed to generate trend report: {e}") from e

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify the integrity of the cryptographic hash chain.

        Returns:
            Tuple[bool, List[str]]: A tuple of (success, list of errors).
        """
        errors = []
        try:
            with self.db_manager.session(self.config) as session:
                entries = session.query(AuditEntry).order_by(AuditEntry.id.asc()).all()

                expected_prev_hash = "0" * 64
                for e in entries:
                    # 1. Verify previous hash matching
                    if e.previous_hash != expected_prev_hash:
                        errors.append(
                            f"Chain broken at entry ID {e.id}: "
                            f"previous_hash '{e.previous_hash}' does not match expected '{expected_prev_hash}'"
                        )

                    # 2. Recalculate hash of current entry
                    payload = f"{e.timestamp.isoformat()}{e.action}{e.details}{e.previous_hash}"
                    calculated_hash = hashlib.sha256(payload.encode()).hexdigest()

                    # 3. Verify current hash matching
                    if e.hash != calculated_hash:
                        errors.append(
                            f"Hash mismatch at entry ID {e.id}: "
                            f"calculated hash '{calculated_hash}' does not match recorded '{e.hash}'"
                        )

                    # The expected previous hash for next entry is the hash of the current entry
                    expected_prev_hash = e.hash or ""
        except Exception as e:
            if isinstance(e, DatabaseException):
                raise
            raise DatabaseException(f"Failed to verify cryptographic chain integrity: {e}") from e

        return len(errors) == 0, errors
