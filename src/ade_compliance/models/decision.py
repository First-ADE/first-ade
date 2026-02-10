from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Decision(BaseModel):
    axiom_id: str
    rationale: str
    criticality: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def requires_human_review(self) -> bool:
        return self.criticality in ["high", "critical"]


class Override(Decision):
    expires_in_days: int = 90
    scope: Optional[str] = None

    @property
    def is_active(self) -> bool:
        # Simplified: Assumes creation time is now
        # Real impl would check (timestamp + expires) > now
        return True


class Attestation(BaseModel):
    agent_id: str
    task_id: str
    confidence: float
    axioms_applied: List[str] = []
    status: str = "pending"  # pending | passed | failed | escalated
    timestamp: datetime = Field(default_factory=datetime.utcnow)
