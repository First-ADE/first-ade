"""Centralized Domain Models for ADE Compliance.

Consolidates and encapsulates all domain and data schemas (Axioms, Violations,
Decisions, Overrides, Attestations, and Reports) into a single, cohesive module.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class ViolationState(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    OVERRIDDEN = "overridden"


class TraceLink(BaseModel):
    source: str
    target: str
    type: str


class Axiom(BaseModel):
    id: str
    name: str
    category: str
    severity: str
    enabled: bool = True
    description: Optional[str] = None


class Violation(BaseModel):
    axiom_id: str
    file_path: str
    message: str
    severity: str = "medium"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    state: ViolationState = ViolationState.NEW

    def acknowledge(self):
        self.state = ViolationState.ACKNOWLEDGED

    def resolve(self):
        self.state = ViolationState.RESOLVED

    def override(self):
        self.state = ViolationState.OVERRIDDEN


class Decision(BaseModel):
    axiom_id: str
    rationale: str
    criticality: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    @property
    def requires_human_review(self) -> bool:
        return self.criticality in ["high", "critical"]


class Override(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    axiom_id: str
    scope_type: str  # FILE | DIRECTORY | COMPONENT
    scope_value: str
    rationale: str
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at: datetime
    is_permanent: bool = False
    permanent_justification: Optional[str] = None
    revoked_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_permanent(self) -> "Override":
        if self.is_permanent and not self.permanent_justification:
            raise ValueError("permanent_justification is required when is_permanent is True")
        return self

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.is_permanent:
            return True
        return datetime.now(timezone.utc).replace(tzinfo=None) < self.expires_at


class Attestation(BaseModel):
    agent_id: str
    task_id: str
    confidence: float
    axioms_applied: List[str] = []
    status: str = "pending"  # pending | passed | failed | escalated
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ComplianceReport(BaseModel):
    schema_version: str = Field(default="1.0.0", alias="version")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        alias="timestamp",
    )
    repo_root: str
    commit_sha: Optional[str] = None
    check_duration_ms: int = 0
    checks_run: List[Dict[str, Any]] = Field(default_factory=list)
    violations: List[Violation] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)
    traceability_matrix: Dict[str, Dict[str, List[str]]] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    attestation: Optional[Any] = None

    model_config = {"populate_by_name": True}

    @property
    def version(self) -> str:
        return self.schema_version

    @property
    def timestamp(self) -> datetime:
        return self.generated_at

    def generate_summary(self) -> str:
        self.summary = {
            "total": len(self.violations),
            "new": sum(1 for v in self.violations if v.state == ViolationState.NEW),
            "acknowledged": sum(1 for v in self.violations if v.state == ViolationState.ACKNOWLEDGED),
            "resolved": sum(1 for v in self.violations if v.state == ViolationState.RESOLVED),
            "overridden": sum(1 for v in self.violations if v.state == ViolationState.OVERRIDDEN),
        }
        return f"Violations: {self.summary['total']} (New: {self.summary['new']}, Resolved: {self.summary['resolved']})"
