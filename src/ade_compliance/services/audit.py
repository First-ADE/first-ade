import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..config import Config

Base = declarative_base()


class AuditEntry(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
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
        session = self.Session()
        try:
            # Get last hash
            last_entry = session.query(AuditEntry).order_by(AuditEntry.id.desc()).first()
            prev_hash = last_entry.hash if last_entry else "0" * 64

            # Serialize details
            details_json = json.dumps(details, sort_keys=True)

            # Calculate new hash
            timestamp = datetime.utcnow()
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
