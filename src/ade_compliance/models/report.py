from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .axiom import Violation


class ComplianceReport(BaseModel):
    schema_version: str = Field(default="1.0.0", alias="version")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), alias="timestamp")
    repo_root: str
    commit_sha: Optional[str] = None
    check_duration_ms: int = 0
    checks_run: List[Dict[str, Any]] = []
    violations: List[Violation] = []
    summary: Dict[str, int] = {}
    traceability_matrix: Dict[str, Dict[str, List[str]]] = {}
    metrics: Dict[str, Any] = {}
    attestation: Optional[Any] = None

    model_config = {"populate_by_name": True}

    @property
    def version(self) -> str:
        return self.schema_version

    @property
    def timestamp(self) -> datetime:
        return self.generated_at

    def generate_summary(self):
        self.summary = {
            "total": len(self.violations),
            "new": sum(1 for v in self.violations if v.state == "new"),
            "resolved": sum(1 for v in self.violations if v.state == "resolved"),
        }
        return f"Violations: {self.summary['total']} (New: {self.summary['new']}, Resolved: {self.summary['resolved']})"
