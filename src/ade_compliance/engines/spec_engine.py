from pathlib import Path
from typing import List
from ..models.axiom import Violation, ViolationState
from .base import BaseEngine

class SpecEngine(BaseEngine):
    async def check(self, files: List[str]) -> List[Violation]:
        if not self.should_run():
            return []
            
        violations = []
        
        # Real implementation:
        specs = list(Path(".").glob("specs/**/*.md")) + list(Path(".").glob("spec.md"))
        if not specs:
             violations.append(Violation(
                 axiom_id="\u03a0.1.1",
                 file_path=".",
                 message="No specification found",
                 state=ViolationState.NEW
             ))
             
        return violations
