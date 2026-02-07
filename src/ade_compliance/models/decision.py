from datetime import datetime
from typing import Optional
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
        return True

class Attestation(BaseModel):
    agent_id: str
    task_id: str
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
