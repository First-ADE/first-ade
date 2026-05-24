# implements: FR-015
# traces_to: Π.2.2

"""Forbidden API Call Checker Engine.

Performs AST-based static analysis on Python test files to detect non-deterministic
or externally-dependent API calls that violate test isolation and determinism
requirements (FR-015, Principle III).

Forbidden patterns include:
- time.sleep() — non-deterministic timing dependency
- datetime.now() / datetime.utcnow() — non-deterministic time source
- Unseeded random.* calls — non-deterministic RNG
- Direct network I/O (requests.*, httpx.*, socket.*, urllib.*)
- os.system() — external process invocation

Files in src/ directories are NOT checked (production code may legitimately use
these APIs). Only files under tests/ directories are scanned.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

from ..models import Severity, Violation, ViolationState
from ..utils.path import normalize_project_path
from .base import BaseEngine

# Mapping of forbidden attribute calls to human-readable reasons.
# Keys are (module, attribute) tuples for calls like module.attribute().
FORBIDDEN_ATTR_CALLS: Dict[Tuple[str, str], str] = {
    ("time", "sleep"): "Non-deterministic timing dependency (use unittest.mock to patch time.sleep)",
    ("datetime", "now"): "Non-deterministic time source (use freezegun or unittest.mock)",
    ("datetime", "utcnow"): "Non-deterministic time source (use freezegun or unittest.mock)",
    ("os", "system"): "External process call in test (use subprocess mock or avoid)",
    ("requests", "get"): "Direct HTTP call in test (use responses library or unittest.mock)",
    ("requests", "post"): "Direct HTTP call in test (use responses library or unittest.mock)",
    ("requests", "put"): "Direct HTTP call in test (use responses library or unittest.mock)",
    ("requests", "delete"): "Direct HTTP call in test (use responses library or unittest.mock)",
    ("requests", "patch"): "Direct HTTP call in test (use responses library or unittest.mock)",
    ("requests", "head"): "Direct HTTP call in test (use responses library or unittest.mock)",
    ("httpx", "get"): "Direct HTTP call in test (use respx library or unittest.mock)",
    ("httpx", "post"): "Direct HTTP call in test (use respx library or unittest.mock)",
    ("httpx", "put"): "Direct HTTP call in test (use respx library or unittest.mock)",
    ("httpx", "delete"): "Direct HTTP call in test (use respx library or unittest.mock)",
    ("socket", "connect"): "Direct network I/O in test (mock socket connections)",
    ("socket", "create_connection"): "Direct network I/O in test (mock socket connections)",
    ("urllib", "urlopen"): "Direct network I/O in test (use unittest.mock)",
}

# Random module functions that are forbidden without a preceding seed() call.
RANDOM_FUNCTIONS: Set[str] = {
    "random",
    "randint",
    "choice",
    "choices",
    "shuffle",
    "sample",
    "uniform",
    "randrange",
    "gauss",
    "triangular",
    "betavariate",
    "expovariate",
    "gammavariate",
    "lognormvariate",
    "normalvariate",
    "vonmisesvariate",
    "paretovariate",
    "weibullvariate",
}

# Names that are imported via `from time import sleep` style imports.
# Maps imported name -> (original_module, original_attr)
BARE_NAME_FORBIDDEN: Dict[str, Tuple[str, str]] = {
    "sleep": ("time", "sleep"),
}


class ForbiddenAPIEngine(BaseEngine):
    """Engine that scans Python test files for forbidden API calls.

    Uses the stdlib ast module to parse and walk the AST, detecting calls
    that violate test determinism requirements.
    """

    def scan_source(self, source: str, file_path: str) -> List[Violation]:
        """Scan Python source code for forbidden API calls.

        Args:
            source: The Python source code string.
            file_path: The file path (used for violation reporting).

        Returns:
            List of Violation objects for each forbidden call found.
        """
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            # Gracefully skip files with syntax errors
            return []

        violations: List[Violation] = []
        # Track from-imports to resolve bare name calls
        from_imports = self._collect_from_imports(tree)
        # Check if random.seed() is called anywhere in the file
        has_random_seed = self._has_random_seed(tree, from_imports)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            found = self._check_call_node(node, file_path, from_imports, has_random_seed)
            if found:
                violations.append(found)

        return violations

    async def check(self, files: List[str]) -> List[Violation]:
        """Run forbidden API checks against the provided files.

        Only checks Python files under tests/ directories.
        """
        if not self.should_run():
            return []

        violations: List[Violation] = []

        for file_path in files:
            norm_path = normalize_project_path(file_path)

            # Only check test files
            if not norm_path.startswith("tests/"):
                continue

            # Only check Python files
            if not norm_path.endswith(".py"):
                continue

            path = Path(file_path)
            if not path.exists():
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            violations.extend(self.scan_source(content, norm_path))

        return violations

    def _collect_from_imports(self, tree: ast.AST) -> Dict[str, Tuple[str, str]]:
        """Collect `from X import Y` statements to track bare name origins.

        Returns a mapping of imported name -> (module, original_name).
        Example: `from time import sleep` -> {"sleep": ("time", "sleep")}
        """
        from_imports: Dict[str, Tuple[str, str]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    # Use the alias name if renamed, otherwise the original
                    local_name = alias.asname if alias.asname else alias.name
                    from_imports[local_name] = (node.module, alias.name)

        return from_imports

    def _has_random_seed(self, tree: ast.AST, from_imports: Dict[str, Tuple[str, str]]) -> bool:
        """Check if random.seed() is called anywhere in the module.

        This is a simplistic whole-file check — if seed() is called at module
        level or in any function, all random calls are considered safe.
        """
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            # Check random.seed()
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "random" and node.func.attr == "seed":
                        return True

            # Check bare seed() from `from random import seed`
            if isinstance(node.func, ast.Name):
                if node.func.id == "seed":
                    origin = from_imports.get("seed")
                    if origin and origin[0] == "random":
                        return True

        return False

    def _check_call_node(
        self,
        node: ast.Call,
        file_path: str,
        from_imports: Dict[str, Tuple[str, str]],
        has_random_seed: bool,
    ) -> Violation | None:
        """Check a single ast.Call node for forbidden patterns.

        Returns a Violation if the call is forbidden, or None otherwise.
        """
        line_no = getattr(node, "lineno", 0)

        # --- Check attribute calls: module.func() ---
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            value = node.func.value

            # Simple case: direct module.func() like time.sleep()
            if isinstance(value, ast.Name):
                module_name = value.id
                key = (module_name, attr_name)

                # Special handling for random module
                if module_name == "random" and attr_name in RANDOM_FUNCTIONS:
                    if not has_random_seed:
                        return Violation(
                            axiom_id="Π.2.2",
                            file_path=file_path,
                            message=(
                                f"Forbidden API call: random.{attr_name}() at line {line_no}. "
                                f"Unseeded random call (seed with random.seed() for determinism)"
                            ),
                            severity=Severity.CRITICAL,
                            state=ViolationState.NEW,
                        )
                    return None

                # Check against forbidden attribute calls table
                if key in FORBIDDEN_ATTR_CALLS:
                    reason = FORBIDDEN_ATTR_CALLS[key]
                    return Violation(
                        axiom_id="Π.2.2",
                        file_path=file_path,
                        message=f"Forbidden API call: {module_name}.{attr_name}() at line {line_no}. {reason}",
                        severity=Severity.CRITICAL,
                        state=ViolationState.NEW,
                    )

            # Chained case: module.submodule.func() like datetime.datetime.utcnow()
            if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
                outer_module = value.value.id
                inner_attr = value.attr
                # e.g., datetime.datetime.utcnow()
                key = (inner_attr, attr_name)
                if key in FORBIDDEN_ATTR_CALLS:
                    reason = FORBIDDEN_ATTR_CALLS[key]
                    return Violation(
                        axiom_id="Π.2.2",
                        file_path=file_path,
                        message=(
                            f"Forbidden API call: {outer_module}.{inner_attr}.{attr_name}() at line {line_no}. {reason}"
                        ),
                        severity=Severity.CRITICAL,
                        state=ViolationState.NEW,
                    )

        # --- Check bare name calls: func() from `from X import Y` ---
        if isinstance(node.func, ast.Name):
            func_name = node.func.id

            # Check if this bare name was imported from a forbidden module
            if func_name in BARE_NAME_FORBIDDEN:
                module, orig_name = BARE_NAME_FORBIDDEN[func_name]
                reason = FORBIDDEN_ATTR_CALLS.get((module, orig_name), "Forbidden API call")
                return Violation(
                    axiom_id="Π.2.2",
                    file_path=file_path,
                    message=f"Forbidden API call: {func_name}() (from {module}) at line {line_no}. {reason}",
                    severity=Severity.CRITICAL,
                    state=ViolationState.NEW,
                )

            # Check from-imported forbidden functions
            origin = from_imports.get(func_name)
            if origin:
                module, orig_name = origin
                # Check random functions
                if module == "random" and orig_name in RANDOM_FUNCTIONS:
                    if not has_random_seed:
                        return Violation(
                            axiom_id="Π.2.2",
                            file_path=file_path,
                            message=(
                                f"Forbidden API call: {func_name}() (from random) at line {line_no}. "
                                f"Unseeded random call (seed with random.seed() for determinism)"
                            ),
                            severity=Severity.CRITICAL,
                            state=ViolationState.NEW,
                        )
                    return None

                # Check other forbidden calls
                key = (module, orig_name)
                if key in FORBIDDEN_ATTR_CALLS:
                    reason = FORBIDDEN_ATTR_CALLS[key]
                    return Violation(
                        axiom_id="Π.2.2",
                        file_path=file_path,
                        message=f"Forbidden API call: {func_name}() (from {module}) at line {line_no}. {reason}",
                        severity=Severity.CRITICAL,
                        state=ViolationState.NEW,
                    )

        return None
