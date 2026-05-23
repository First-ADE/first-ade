from datetime import datetime
from typing import List, Optional

import uuid
from pydantic import BaseModel, Field, model_validator


class Decision(BaseModel):
    axiom_id: str
    rationale: str
    criticality: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

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
    created_at: datetime = Field(default_factory=datetime.utcnow)
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
        return datetime.utcnow() < self.expires_at


class Attestation(BaseModel):
    agent_id: str
    task_id: str
    confidence: float
    axioms_applied: List[str] = []
    status: str = "pending"  # pending | passed | failed | escalated
    timestamp: datetime = Field(default_factory=datetime.utcnow)
