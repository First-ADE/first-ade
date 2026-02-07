from typing import List, Optional
from pathlib import Path
from .base import BaseEngine
from ..models.axiom import Violation, ViolationState

class TestEngine(BaseEngine):
    async def check(self, files: List[str]) -> List[Violation]:
        if not self.should_run():
            return []
            
        violations = []
        for file_path in files:
            # Only check impl files (heuristic: in src/ and .py)
            if not file_path.startswith("src/") or not file_path.endswith(".py"):
                continue
                
            test_path = self.find_test_file(file_path)
            
            if not test_path:
                violations.append(Violation(
                    axiom_id="\u03a0.2.1",
                    file_path=file_path,
                    message=f"Missing test file for {file_path}",
                    state=ViolationState.NEW
                ))
                continue
                
            # Check determinism in test file
            try:
                path = Path(test_path)
                if path.exists():
                     with open(path, "r", encoding="utf-8") as f:
                         content = f.read()
                         if "time.sleep" in content or "requests.get" in content:
                             violations.append(Violation(
                                axiom_id="\u03a0.3.1",
                                file_path=test_path,
                                message="Non-deterministic code detected (sleep/network)",
                                state=ViolationState.NEW
                             ))
            except Exception:
                pass
                
        return violations
    
    def find_test_file(self, impl_path: str) -> Optional[str]:
        p = Path(impl_path)
        name = p.name
        test_name = f"test_{name}"
        
        candidates = [
            f"tests/unit/{test_name}",
            f"tests/{test_name}",
            f"tests/unit/models/{test_name}",
            f"tests/unit/services/{test_name}",
            f"tests/unit/engines/{test_name}",
        ]
        
        for c in candidates:
            if Path(c).exists():
                return c
        return None
