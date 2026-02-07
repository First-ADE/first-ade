from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

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
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    state: ViolationState = ViolationState.NEW
    
    def acknowledge(self):
        self.state = ViolationState.ACKNOWLEDGED
        
    def resolve(self):
        self.state = ViolationState.RESOLVED
        
    def override(self):
        self.state = ViolationState.OVERRIDDEN
