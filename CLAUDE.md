# Claude Agent Guidelines: First-ADE Compliance Framework

This document outlines the strict technical, architectural, and procedural standards for development on the **First-ADE Compliance Framework** codebase using Claude Code and anthropic agents.

---

## 🏛️ Axiom-Driven Engineering (ADE) Context

Before making any functional or structural changes, all agents must load and conform to the ADE core documents:
1. **Constitution**: `.specify/memory/constitution.md` — 7 binding architectural principles
2. **Axioms**: `docs/AXIOMS.md` — 5 foundational software design truths (Σ.1–Σ.5)
3. **Postulates**: `docs/POSTULATES.md` — three orders of derived rules (Π.x.y)
4. **Templates**: `.specify/templates/` — canonical plan, specs, and tasks structures

---

## 🚀 Unified Dev Quality Runner

First-ADE provides a unified orchestrator script that MUST be run locally before any git push or PR request. It verifies formatting, syntax, typechecking, tests, and compliance in one run.

### Standard Quality Execution
```powershell
./run-checks.ps1
```

### Auto-fixing Formatting & Linting
If formatting or minor linting warnings fail, run the auto-fixer:
```powershell
./run-checks.ps1 -Fix
```

---

## 🔍 Individual CLI Command Reference

If you need to run specific tools manually:

### 1. Code Quality & Format
- **Linting**: `uv run ruff check .`
- **Formatting**: `uv run ruff format .` (or `uv run ruff format --check .` for verification)
- **Strict Type Checking**: `uv run mypy src/`

### 2. Running the Test Suite
Tests must pass with **zero warnings**:
```powershell
uv run pytest
```

### 3. Compliance Gateway CLI
Run the local orchestrator directly:
- **All Engines**: `uv run ade-compliance check-all src/`
- **Spec Only**: `uv run ade-compliance check-spec src/`
- **Tests Only**: `uv run ade-compliance check-test src/`
- **Traceability Matrix**: `uv run ade-compliance check-traceability src/`
- **ADR Only**: `uv run ade-compliance check-adr src/`

---

## 📐 Strict Coding & Design Guidelines

1. **Test-First (TDD) Alignment (Principle III)**:
   - Writing tests *before* the implementation code is mandatory. All staging code changes must have matching unit or integration test assertions in the `tests/` directory.
2. **Zero Warnings Policy (Principle I / CONTRIBUTING.md)**:
   - All quality tests must pass cleanly. Any compiler, type, lint, or deprecation warnings are considered a compliance failure and must be remediated.
3. **Traceability Annotations (Principle VI)**:
   - All source code and test files must contain explicit trace comments linking them to axioms and requirements:
     - `# implements: FR-XXX`
     - `# traces_to: Π.X.Y`
4. **Architect SSO & Bypasses (Principles VI/VII)**:
   - Any manual exception/bypass override created via the API or CLI must validate SSO authenticity. Bypasses must include SSO validation headers and have structured rationales ($\geq 20$ characters).

---

## 🔒 Git Mechanics & Workspace Protection

All agents must strictly follow these git hygiene rules:

1. **Dedicated Feature Branches**:
   - Never commit directly to `main`. Create branches branching off of `origin/main` using the spec-kit naming pattern: `###-short-name` (e.g. `002-git-compliance`).
2. **Git Commit Signing (Mandatory)**:
   - All commits must have verified SSH signatures. Ensure your git configuration maps to:
     - `gpg.format=ssh`
     - `user.signingkey` pointing to the workspace `.ssh/*.pub` key (e.g. `C:\Users\bfoxt\.ssh\id_ed25519_vindicta.pub`).
3. **Git Isolation (Concurrency Safeguard)**:
   - **NEVER use `git add .` or `git commit -a`.**
   - You must only `git add` the explicit files you created or modified in the current task. This isolates concurrent agent work.
4. **Prevent Tracked Cache Contamination**:
   - Ensure `**/__pycache__/`, `*.pyc`, and `*.pycc` are explicitly added to `.gitignore`. Check untracked files regularly (`git status -s`).

---

## 🛡️ OOP Refactoring & Development Safeguards

To prevent regressions, timing drifts, connection leaks, and test isolation breaks, all development must adhere to these structural safeguards:

1. **Thread-Safe Scoped Singleton Database Manager**:
   - Never instantiate raw SQLAlchemy engines or call `create_engine` directly in services.
   - Always route session management through the thread-safe `DatabaseManager` singleton class.
   - To guarantee complete test isolation between concurrent unit tests, `DatabaseManager` must cache engines by a compound key of `(id(config), db_path_str)`.
2. **Programmatic Schema Migrations**:
   - Never run `Base.metadata.create_all()` directly on production engine setups. Always route database setups through programmatic Alembic migrations (`run_migrations(engine)`) to enable self-healing auto-stamping of legacy databases.
3. **Polymorphic Base Service Pattern**:
   - All services must inherit from the `BaseService` abstract class (`src/ade_compliance/services/base.py`).
   - Use the lazy-loaded, cached property `self.audit` to completely eliminate circular dependency imports.
4. **Semantic Exception Multi-Inheritance**:
   - Raise custom, domain-specific exception classes (from `src/ade_compliance/exceptions.py`) instead of generic built-ins.
   - Custom exceptions MUST implement multiple inheritance, inheriting from both `ADEException` and standard built-ins (e.g. `ValueError`, `RuntimeError`, `OSError`) to maintain seamless backward compatibility with standard error catching blocks and test suites.
5. **Path Normalization Safeguards**:
   - Always pass file and directory paths through `normalize_project_path` before evaluating compliance scope matches or engine checks. This blocks bypasses resulting from path representation variations (absolute paths vs. `./` prefixes).
6. **Bytecode Cache Purging**:
   - When modifying class constructors or module structures, forcefully clear the python bytecode cache (`Remove-Item -Recurse -Force __pycache__`) to prevent stale compiled modules from polluting pytest loading sequences.
