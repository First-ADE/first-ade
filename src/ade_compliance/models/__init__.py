# implements: FR-007
# traces_to: Π.3.1

"""Centralized Domain Models for ADE Compliance.

Consolidates and encapsulates all domain and data schemas (Axioms, Violations,
Decisions, Overrides, Attestations, and Reports) into a single, cohesive module.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ViolationState(str, Enum):
    """Lifecycle states for a compliance violation."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    OVERRIDDEN = "overridden"


class Severity(str, Enum):
    """Severity levels for violations and axiom rules."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Criticality(str, Enum):
    """Criticality levels for compliance decisions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttestationStatus(str, Enum):
    """Status values for agent attestations."""

    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    ESCALATED = "escalated"


class ScopeType(str, Enum):
    """Override scope types defining the boundary of a compliance exception."""

    FILE = "FILE"
    DIRECTORY = "DIRECTORY"
    COMPONENT = "COMPONENT"


class InvalidStateTransition(Exception):
    """Raised when a Violation state transition is not permitted."""


class TraceLink(BaseModel):
    """A directed traceability link between a source artifact and a target."""

    source: str
    target: str
    type: str


class Axiom(BaseModel):
    """A compliance axiom (rule) that can be checked by an engine."""

    id: str
    name: str
    category: str
    severity: str
    enabled: bool = True
    description: str | None = None


class Violation(BaseModel):
    """A detected compliance violation with a guarded lifecycle state machine.

    Valid transitions:
        NEW → ACKNOWLEDGED → RESOLVED  (standard lifecycle)
        NEW → OVERRIDDEN               (human override)
        ACKNOWLEDGED → OVERRIDDEN       (human override)
        RESOLVED and OVERRIDDEN are terminal states.
    """

    axiom_id: str
    file_path: str
    message: str
    severity: Severity = Severity.MEDIUM
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    state: ViolationState = ViolationState.NEW
    resolved_at: datetime | None = None

    def acknowledge(self) -> None:
        """Transition from NEW → ACKNOWLEDGED."""
        if self.state != ViolationState.NEW:
            raise InvalidStateTransition(f"Cannot acknowledge from state '{self.state.value}'; must be 'new'")
        self.state = ViolationState.ACKNOWLEDGED

    def resolve(self) -> None:
        """Transition from ACKNOWLEDGED → RESOLVED."""
        if self.state != ViolationState.ACKNOWLEDGED:
            raise InvalidStateTransition(f"Cannot resolve from state '{self.state.value}'; must be 'acknowledged'")
        self.state = ViolationState.RESOLVED
        self.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def override(self) -> None:
        """Transition from NEW or ACKNOWLEDGED → OVERRIDDEN."""
        if self.state in (ViolationState.RESOLVED, ViolationState.OVERRIDDEN):
            raise InvalidStateTransition(f"Cannot override from terminal state '{self.state.value}'")
        self.state = ViolationState.OVERRIDDEN
        self.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)


class Decision(BaseModel):
    """A compliance decision record with criticality-based routing.

    Decisions with ``"high"`` or ``"critical"`` criticality require
    Human Architect review via the escalation service.
    """

    axiom_id: str
    rationale: str
    criticality: Criticality
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    @property
    def requires_human_review(self) -> bool:
        """Return True if this decision requires Human Architect review."""
        return self.criticality in (Criticality.HIGH, Criticality.CRITICAL)


class Override(BaseModel):
    """A compliance violation override scoped to a file, directory, or component.

    Permanent overrides require a ``permanent_justification`` that is
    non-empty and non-whitespace.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    axiom_id: str
    scope_type: ScopeType
    scope_value: str
    rationale: str
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at: datetime
    is_permanent: bool = False
    permanent_justification: str | None = None
    revoked_at: datetime | None = None

    @model_validator(mode="after")
    def validate_permanent(self) -> "Override":
        """Ensure permanent overrides include a substantive elevated justification."""
        if self.is_permanent:
            justification = (self.permanent_justification or "").strip()
            if not justification:
                raise ValueError("permanent_justification is required when is_permanent is True")
            if not (justification.startswith("SSO-PR-") or justification.startswith("SSO-SIG-")):
                raise ValueError(
                    "permanent_justification must start with either 'SSO-PR-' or 'SSO-SIG-' "
                    "for elevated justification validation."
                )
        return self

    @property
    def is_active(self) -> bool:
        """Check whether this override is currently in effect."""
        if self.revoked_at is not None:
            return False
        if self.is_permanent:
            return True
        return datetime.now(timezone.utc).replace(tzinfo=None) < self.expires_at


class Attestation(BaseModel):
    """An agent's compliance attestation for a completed task.

    Confidence is bounded to ``[0.0, 1.0]``. Values below the escalation
    threshold (0.7) trigger automatic escalation to Human Architect.
    """

    agent_id: str
    task_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    axioms_applied: list[str] = []
    status: AttestationStatus = AttestationStatus.PENDING
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ComplianceReport(BaseModel):
    """Aggregate compliance report produced by the orchestrator.

    Supports Pydantic field aliases (``version`` / ``timestamp``) for
    backward-compatible serialization via ``model_dump(by_alias=True)``.
    """

    schema_version: str = Field(default="1.0.0", alias="version")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        alias="timestamp",
    )
    repo_root: str
    commit_sha: str | None = None
    check_duration_ms: int = 0
    checks_run: list[dict[str, object]] = Field(default_factory=list)
    violations: list[Violation] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)
    traceability_matrix: dict[str, dict[str, list[str]]] = Field(default_factory=dict)
    metrics: dict[str, object] = Field(default_factory=dict)
    attestation: Attestation | None = None

    model_config = {"populate_by_name": True}

    @property
    def version(self) -> str:
        """Alias accessor for ``schema_version``."""
        return self.schema_version

    @property
    def timestamp(self) -> datetime:
        """Alias accessor for ``generated_at``."""
        return self.generated_at

    def generate_summary(self) -> str:
        """Generate and cache a violation summary, returning a human-readable string."""
        self.summary = {
            "total": len(self.violations),
            "new": sum(1 for v in self.violations if v.state == ViolationState.NEW),
            "acknowledged": sum(1 for v in self.violations if v.state == ViolationState.ACKNOWLEDGED),
            "resolved": sum(1 for v in self.violations if v.state == ViolationState.RESOLVED),
            "overridden": sum(1 for v in self.violations if v.state == ViolationState.OVERRIDDEN),
        }
        return f"Violations: {self.summary['total']} (New: {self.summary['new']}, Resolved: {self.summary['resolved']})"


__all__ = [
    "Attestation",
    "AttestationStatus",
    "Axiom",
    "ComplianceReport",
    "Criticality",
    "Decision",
    "InvalidStateTransition",
    "Override",
    "ScopeType",
    "Severity",
    "TraceLink",
    "Violation",
    "ViolationState",
]
