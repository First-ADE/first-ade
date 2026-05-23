import subprocess
from typing import List

from ..models.axiom import Violation, ViolationState
from .base import BaseEngine


class ADREngine(BaseEngine):
    """Engine to enforce postulate Π.3.1 (ADRs required for all architectural changes)."""

    async def check(self, files: List[str]) -> List[Violation]:
        if not self.should_run():
            return []

        violations = []

        # Heuristic for detecting architectural files
        architectural_files = []
        adr_files = []

        for f in files:
            path_str = f.replace("\\", "/").strip("/")
            
            # 1. Standard config/meta architectural files
            if path_str in ("pyproject.toml", ".ade-compliance.yml", "setup.py"):
                architectural_files.append(f)
            
            # 2. Structural models and engines changes
            elif path_str.startswith("src/ade_compliance/models/") or path_str.startswith("src/ade_compliance/engines/"):
                architectural_files.append(f)

            # 3. Detect changes in ADR directory
            elif path_str.startswith("docs/decisions/") and path_str.endswith(".md"):
                adr_files.append(f)

        # If there are architectural modifications but no corresponding ADR file in checked list
        if architectural_files and not adr_files:
            violations.append(
                Violation(
                    axiom_id="Π.3.1",
                    file_path=architectural_files[0],
                    message=(
                        f"Architectural change detected in '{architectural_files[0]}', "
                        f"but no ADR created or modified under 'docs/decisions/'. "
                        f"Postulate Π.3.1 requires recording ADRs for all architectural changes."
                    ),
                    state=ViolationState.NEW,
                )
            )
            return violations

        # If an ADR is added/modified, or if we want to run checks on the whole repo
        # Execute pyadr validation using subprocess to guarantee format sanity
        if adr_files:
            try:
                # Run check-adr-repo from pyadr
                res = subprocess.run(["pyadr", "check-adr-repo"], capture_output=True, text=True)
                if res.returncode != 0:
                    violations.append(
                        Violation(
                            axiom_id="Π.3.2",
                            file_path=adr_files[0],
                            message=(
                                f"pyadr check-adr-repo failed on the ADR repository.\n"
                                f"Error Details:\n{res.stderr or res.stdout}"
                            ),
                            state=ViolationState.NEW,
                        )
                    )
            except Exception as e:
                # If pyadr command itself fails/not found, log it as format violation
                violations.append(
                    Violation(
                        axiom_id="Π.3.2",
                        file_path=adr_files[0],
                        message=f"Error executing pyadr validation check: {e}",
                        state=ViolationState.NEW,
                    )
                )

        return violations
