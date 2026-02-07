from pathlib import Path
from typing import List
from ..models.axiom import Violation, ViolationState
from .base import BaseEngine

class SpecEngine(BaseEngine):
    async def check(self, files: List[str]) -> List[Violation]:
        if not self.should_run():
            return []
            
        violations = []
        # Naive check: Look for spec.md or *.feature in obvious places
        # In reality, might search up from file path or checks repo root
        
        # We assume files are relative to repo root or we check specific locations
        # For this MVP, we verify if `specs/` exists or `spec.md` exists in root
        
        spec_exists = False
        repo_root = Path(".") # Simplify
        
        # Check standard locations
        if list(repo_root.glob("specs/**/*.md")) or list(repo_root.glob("*.md")):
             # Check content for "Requirement" or "Feature"
             # This is a stub for T026
             spec_exists = True
             
        # Actually, the test mocks glob.
        # Let's match the test expectation: it checks glob("specs/**/*.md") maybe?
        # The test output in Step 187 mocked `pathlib.Path.glob`
        
        # Re-reading test: 
        # with patch("pathlib.Path.glob", return_value=[]): ... missing
        
        # Real implementation:
        specs = list(Path(".").glob("specs/**/*.md")) + list(Path(".").glob("spec.md"))
        if not specs:
             violations.append(Violation(
                 axiom_id="Π.1.1",
                 file_path=".",
                 message="No specification found",
                 state=ViolationState.NEW
             ))
             
        return violations
