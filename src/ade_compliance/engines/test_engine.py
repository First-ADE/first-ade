# implements: FR-002
# traces_to: Π.2.1

from pathlib import Path
from typing import List, Optional

from ..models.axiom import Violation, ViolationState
from .base import BaseEngine


class TestEngine(BaseEngine):
    async def check(self, files: List[str]) -> List[Violation]:
        if not self.should_run():
            return []

        from ..utils.path import normalize_project_path

        violations = []
        for file_path in files:
            norm_path = normalize_project_path(file_path)
            # Only check impl files (heuristic: in src/ and .py)
            if not norm_path.startswith("src/") or not norm_path.endswith(".py"):
                continue

            # Skip package initializers since they generally contain no functional logic
            if Path(file_path).name == "__init__.py":
                continue

            test_path = self.find_test_file(file_path)

            if not test_path:
                violations.append(
                    Violation(
                        axiom_id="Π.2.1",
                        file_path=norm_path,
                        message=f"Missing test file for {norm_path}",
                        state=ViolationState.NEW,
                    )
                )
                continue

            # Check determinism in test file
            try:
                # Naive check for time.sleep or external I/O
                # Ideally use AST parsing, for MVP use string search
                path = Path(test_path)
                if path.exists():  # In tests we mock open, but check logic uses open
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if "time.sleep" in content or "requests.get" in content:
                            violations.append(
                                Violation(
                                    axiom_id="Π.2.2",
                                    file_path=normalize_project_path(test_path),
                                    message="Non-deterministic code detected (sleep/network)",
                                    state=ViolationState.NEW,
                                )
                            )
            except Exception:
                # If file read fails (e.g. mocked in test without file), ignore or ensure mock works
                pass

        return violations

    def find_test_file(self, impl_path: str) -> Optional[str]:
        p = Path(impl_path)
        name = p.name
        basename = p.stem
        test_name = f"test_{name}"

        # Check standard and extended locations to avoid false-positive test omissions
        candidates = [
            f"tests/unit/{test_name}",
            f"tests/unit/test_{basename}_unit.py",
            f"tests/{test_name}",
            f"tests/integration/{test_name}",
            f"tests/unit/models/{test_name}",
            f"tests/unit/services/{test_name}",
            f"tests/unit/engines/{test_name}",
            f"tests/unit/observability/{test_name}",
            f"tests/unit/utils/{test_name}",
        ]

        for c in candidates:
            if Path(c).exists():
                return c
        return None
