"""T051: Override service for compliance framework overrides.

Provides violating rule exception overrides with scope matching, rationale validation,
audit trail logging, and local SQLite DB storage.
Consolidates engine setup using the centralized database manager.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import Boolean, Column, DateTime, String

from ..config import Config
from ..models.decision import Override
from ..services.audit import AuditService
from .db import Base, db_session


class OverrideEntry(Base):
    __tablename__ = "override_log"

    id = Column(String, primary_key=True)
    axiom_id = Column(String, nullable=False)
    scope_type = Column(String, nullable=False)  # FILE | DIRECTORY | COMPONENT
    scope_value = Column(String, nullable=False)
    rationale = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at = Column(DateTime, nullable=False)
    is_permanent = Column(Boolean, default=False)
    permanent_justification = Column(String, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    expiry_notified = Column(Boolean, default=False)


class OverrideService:
    def __init__(self, config: Config):
        self.config = config
        self.audit = AuditService(config)

        from sqlalchemy.orm import sessionmaker

        from .db import Base as db_Base
        from .db import get_engine

        self.engine = get_engine(config)
        db_Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

        # Self-healing migration for legacy databases to insert columns if not present
        try:
            from sqlalchemy import text

            with self.engine.connect() as conn:
                conn.execute(text("ALTER TABLE override_log ADD COLUMN expiry_notified BOOLEAN DEFAULT 0"))
                conn.commit()
        except Exception:
            pass

    def create_override(
        self,
        axiom_id: str,
        scope_type: str,
        scope_value: str,
        rationale: str,
        created_by: str,
        expires_in_days: int = 90,
        is_permanent: bool = False,
        permanent_justification: str = "",
    ) -> Override:
        """Create and persist a violation override."""
        # Validate constraints
        if len(rationale) < 20:
            raise ValueError("Rationale must be at least 20 characters long.")

        if is_permanent and not permanent_justification:
            raise ValueError("permanent_justification is required when is_permanent is True")

        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=expires_in_days)
        override_id = str(uuid.uuid4())

        entry = OverrideEntry(
            id=override_id,
            axiom_id=axiom_id,
            scope_type=scope_type,
            scope_value=scope_value,
            rationale=rationale,
            created_by=created_by,
            expires_at=expires_at,
            is_permanent=is_permanent,
            permanent_justification=permanent_justification if is_permanent else None,
        )

        with db_session(self.config) as session:
            session.add(entry)
            # Fetch created_at populated by DB default
            created_at = entry.created_at or datetime.now(timezone.utc).replace(tzinfo=None)

        # Log to audit trail
        self.audit.log(
            "OVERRIDE_RECORDED",
            {
                "id": override_id,
                "axiom_id": axiom_id,
                "scope_type": scope_type,
                "scope_value": scope_value,
                "rationale": rationale,
                "created_by": created_by,
                "expires_at": expires_at.isoformat(),
                "is_permanent": is_permanent,
                "permanent_justification": permanent_justification if is_permanent else None,
            },
        )

        return Override(
            id=override_id,
            axiom_id=axiom_id,
            scope_type=scope_type,
            scope_value=scope_value,
            rationale=rationale,
            created_by=created_by,
            created_at=created_at,
            expires_at=expires_at,
            is_permanent=is_permanent,
            permanent_justification=permanent_justification if is_permanent else None,
        )

    def get_active_overrides(self) -> List[Override]:
        """Retrieve all currently active (non-expired and non-revoked) overrides."""
        with db_session(self.config) as session:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            entries = session.query(OverrideEntry).filter(OverrideEntry.revoked_at == None).all()

            active = []
            for e in entries:
                is_expired = not e.is_permanent and e.expires_at <= now
                if not is_expired:
                    active.append(
                        Override(
                            id=e.id,
                            axiom_id=e.axiom_id,
                            scope_type=e.scope_type,
                            scope_value=e.scope_value,
                            rationale=e.rationale,
                            created_by=e.created_by,
                            created_at=e.created_at,
                            expires_at=e.expires_at,
                            is_permanent=e.is_permanent,
                            permanent_justification=e.permanent_justification,
                            revoked_at=e.revoked_at,
                        )
                    )
            return active

    def is_override_active(self, axiom_id: str, file_path: str) -> bool:
        """Check if an active override covers this axiom ID and file path."""
        active_list = self.get_active_overrides()
        for o in active_list:
            if o.axiom_id == axiom_id:
                # Match path against scope
                p = file_path.replace("\\", "/").strip("/")
                sv = o.scope_value.replace("\\", "/").strip("/")

                if o.scope_type == "FILE":
                    if p == sv:
                        return True
                elif o.scope_type == "DIRECTORY":
                    if p.startswith(sv + "/") or p == sv:
                        return True
                elif o.scope_type == "COMPONENT":
                    if sv in p:
                        return True
        return False

    def revoke_override(self, override_id: str) -> bool:
        """Manually revoke a compliance override."""
        with db_session(self.config) as session:
            entry = session.query(OverrideEntry).filter(OverrideEntry.id == override_id).first()
            if not entry:
                return False

            now = datetime.now(timezone.utc).replace(tzinfo=None)
            entry.revoked_at = now

        # Log to audit trail
        self.audit.log(
            "OVERRIDE_REVOKED",
            {
                "id": override_id,
                "revoked_at": now.isoformat(),
            },
        )
        return True

    def check_expiring_overrides(self) -> List[Override]:
        """Check for active overrides expiring in <= 7 days and notify via EscalationService."""
        with db_session(self.config) as session:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            seven_days_from_now = now + timedelta(days=7)

            # Query non-permanent overrides expiring within 7 days that haven't been notified yet
            entries = (
                session.query(OverrideEntry)
                .filter(
                    OverrideEntry.revoked_at == None,
                    OverrideEntry.is_permanent == False,
                    OverrideEntry.expires_at <= seven_days_from_now,
                    OverrideEntry.expires_at >= now,
                    OverrideEntry.expiry_notified == False,
                )
                .all()
            )

            expiring = []
            if entries:
                from ..services.escalation import EscalationService

                escalation_service = EscalationService(self.config)

                for e in entries:
                    e.expiry_notified = True
                    expiring.append(
                        Override(
                            id=e.id,
                            axiom_id=e.axiom_id,
                            scope_type=e.scope_type,
                            scope_value=e.scope_value,
                            rationale=e.rationale,
                            created_by=e.created_by,
                            created_at=e.created_at,
                            expires_at=e.expires_at,
                            is_permanent=e.is_permanent,
                            permanent_justification=e.permanent_justification,
                            revoked_at=e.revoked_at,
                        )
                    )

                    # Notify responsible party/architects via EscalationService
                    title = f"[ADE Expiry Warning] Compliance Override ID {e.id} is expiring soon"
                    body = (
                        f"The following compliance override is expiring in less than 7 days "
                        f"and will automatically auto-revert to enforcement:\n\n"
                        f"- **ID**: {e.id}\n"
                        f"- **Axiom**: {e.axiom_id}\n"
                        f"- **Scope**: {e.scope_type} ({e.scope_value})\n"
                        f"- **Rationale**: {e.rationale}\n"
                        f"- **Expiration**: {e.expires_at.isoformat()} UTC\n\n"
                        f"Please review and recreate if a renewal is required."
                    )

                    from ..utils.async_helpers import run_async_safe

                    run_async_safe(escalation_service.escalate(title, body))

            return expiring
