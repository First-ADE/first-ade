# implements: FR-007
# traces_to: Π.3.1

"""Base service class for First-ADE compliance services."""

from typing import Any

from ..config import Config
from .db import DatabaseManager


class BaseService:
    """Base class for all First-ADE compliance services.

    Provides core dependencies and database session management properties,
    ensuring highly cohesive connection lifetimes and robust service boundaries.
    """

    def __init__(self, config: Config):
        self.config = config
        self.db_manager = DatabaseManager()

    @property
    def audit(self) -> Any:
        """Lazy-loaded AuditService instance to avoid circular dependency loops."""
        if not hasattr(self, "_audit_service"):
            from .audit import AuditService

            self._audit_service = AuditService(self.config)
        return self._audit_service
