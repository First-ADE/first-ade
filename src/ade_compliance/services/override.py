"""T051: Override service for compliance framework overrides.

Provides violating rule exception overrides with scope matching, rationale validation,
audit trail logging, and local SQLite DB storage.
"""

import uuid
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import Boolean, Column, DateTime, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from ..config import Config
from ..models.decision import Override
from ..services.audit import AuditService

Base = declarative_base()


class OverrideEntry(Base):
    __tablename__ = "override_log"

    id = Column(String, primary_key=True)
    axiom_id = Column(String, nullable=False)
    scope_type = Column(String, nullable=False)  # FILE | DIRECTORY | COMPONENT
    scope_value = Column(String, nullable=False)
    rationale = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_permanent = Column(Boolean, default=False)
    permanent_justification = Column(String, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    expiry_notified = Column(Boolean, default=False)


class OverrideService:
    def __init__(self, config: Config):
        self.config = config
        self.audit = AuditService(config)
        self.db_path = config.global_settings.audit_path
        
        if self.db_path == ":memory:" or not self.db_path:
            url = "sqlite://"
        else:
            path = self.db_path.replace("\\", "/")
            url = f"sqlite:///{path}"
            
            # ensure dir exists
            import pathlib
            p = pathlib.Path(self.db_path)
            if p.parent and not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(url)
        Base.metadata.create_all(self.engine)
        
        # Self-healing migration for existing databases adding the expiry_notified column
        try:
            with self.engine.connect() as conn:
                conn.execute(text("ALTER TABLE override_log ADD COLUMN expiry_notified BOOLEAN DEFAULT 0"))
                conn.commit()
        except Exception:
            pass

        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

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
        """Create and persist a violation override.
        
        Args:
            axiom_id: Violation rule to override.
            scope_type: FILE | DIRECTORY | COMPONENT.
            scope_value: Target path or component name.
            rationale: Explanation (min 20 characters).
            created_by: Human Architect SSO ID.
            expires_in_days: Validity duration.
            is_permanent: Permanent bypass toggle.
            permanent_justification: Elevated context for permanent overrides.
            
        Returns:
            The created Override model.
        """
        # Validate constraints
        if len(rationale) < 20:
            raise ValueError("Rationale must be at least 20 characters long.")

        if is_permanent and not permanent_justification:
            raise ValueError("permanent_justification is required when is_permanent is True")

        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
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

        session = self.Session()
        try:
            session.add(entry)
            session.commit()
        finally:
            session.close()

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
            created_at=entry.created_at,
            expires_at=expires_at,
            is_permanent=is_permanent,
            permanent_justification=permanent_justification if is_permanent else None,
        )

    def get_active_overrides(self) -> List[Override]:
        """Retrieve all currently active (non-expired and non-revoked) overrides."""
        session = self.Session()
        try:
            now = datetime.utcnow()
            entries = session.query(OverrideEntry).filter(
                OverrideEntry.revoked_at == None
            ).all()

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
        finally:
            session.close()

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
        session = self.Session()
        try:
            entry = session.query(OverrideEntry).filter(OverrideEntry.id == override_id).first()
            if not entry:
                return False

            now = datetime.utcnow()
            entry.revoked_at = now
            session.commit()
            
            # Log to audit trail
            self.audit.log(
                "OVERRIDE_REVOKED",
                {
                    "id": override_id,
                    "revoked_at": now.isoformat(),
                },
            )
            return True
        finally:
            session.close()

    def check_expiring_overrides(self) -> List[Override]:
        """Check for active overrides expiring in <= 7 days and notify via EscalationService."""
        session = self.Session()
        try:
            now = datetime.utcnow()
            seven_days_from_now = now + timedelta(days=7)
            
            # Query non-permanent overrides expiring within 7 days that haven't been notified yet
            entries = session.query(OverrideEntry).filter(
                OverrideEntry.revoked_at == None,
                OverrideEntry.is_permanent == False,
                OverrideEntry.expires_at <= seven_days_from_now,
                OverrideEntry.expires_at >= now,
                OverrideEntry.expiry_notified == False
            ).all()
            
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
                    
                    # Safe async trigger helper
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None
                        
                    if loop and loop.is_running():
                        from concurrent.futures import ThreadPoolExecutor
                        with ThreadPoolExecutor() as executor:
                            executor.submit(lambda: asyncio.run(escalation_service.escalate(title, body))).result()
                    else:
                        asyncio.run(escalation_service.escalate(title, body))
                
                session.commit()
            return expiring
        finally:
            session.close()
