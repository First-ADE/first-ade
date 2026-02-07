from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, Field
from .axiom import Violation

class ComplianceReport(BaseModel):
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    repo_root: str
    violations: List[Violation] = []
    summary: Dict[str, int] = {}
    
    def generate_summary(self):
        self.summary = {
            "total": len(self.violations),
            "new": sum(1 for v in self.violations if v.state == "new"),
            "resolved": sum(1 for v in self.violations if v.state == "resolved"),
        }
        return f"Violations: {self.summary['total']} (New: {self.summary['new']}, Resolved: {self.summary['resolved']})"
