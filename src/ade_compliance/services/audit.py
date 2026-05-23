import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..config import Config
from ..observability.logging import logger

Base = declarative_base()


class AuditEntry(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    action = Column(String)
    details = Column(String)  # JSON
    previous_hash = Column(String)
    hash = Column(String)


class AuditService:
    def __init__(self, config: Config):
        self.db_path = config.global_settings.audit_path
        if self.db_path == ":memory:" or not self.db_path:
            url = "sqlite://"
        else:
            # Handle windows paths
            path = self.db_path.replace("\\", "/")
            url = f"sqlite:///{path}"

            # ensure dir exists
            import pathlib

            p = pathlib.Path(self.db_path)
            if p.parent and not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def log(self, action: str, details: Dict[str, Any]):
        # Log structured JSON to stdout using loguru
        logger.info("audit_event", action=action, details=details)
        session = self.Session()
        try:
            # Get last hash
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
            session.commit()
        finally:
            session.close()

    def get_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        session = self.Session()
        try:
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
        finally:
            session.close()

    def get_trend_report(self, days: int = 30) -> Dict[str, Any]:
        """Aggregate compliance metrics and trends over the last specified number of days."""
        session = self.Session()
        try:
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
                except Exception:
                    pass

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
        finally:
            session.close()
