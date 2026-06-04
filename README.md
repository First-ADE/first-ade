# First-ADE (Agentic Development Environment)

First-ADE is a **local-first, mathematically sound compliance gateway and verification sandbox** designed to ensure absolute alignment between specifications (intent) and code (implementation) in agentic development environments.

---

## 👁️ Why First-ADE?

When autonomous AI agents generate code at scale, traditional testing is not enough. First-ADE wraps the developer workflow in a mathematical sandbox:
1.  **State Simulation (Approach A)**: Traces object and memory state mutations locally, proving the code matches the agent's pre-execution predictions and preventing side-effects.
2.  **Symbolic Proofs (Approach B)**: Extracts the control flow graph from Python ASTs and uses the **Z3 SMT solver** to statically prove that the code always satisfies spec invariants and decorators.
3.  **Git-Native Governance**: Overrides and compliance history are version-controlled directly inside the Git repository (no databases or SaaS servers required), making compliance auditable via Pull Requests.

---

## 📐 Monorepo Architecture

First-ADE is packaged as a single, self-contained open-source monorepo:

```
                         first-ade (Single Repository)
                         ├── cli/          # Core CLI python verification engine
                         ├── mcp/          # Model Context Protocol server for LLMs
                         └── github-action/# PR-level compliance action
```

-   **`/cli`**: The Python verification CLI (`ade-compliance`) executing specification audits, state simulation checks, and AST-to-SMT proofs.
-   **`/mcp`**: The Model Context Protocol (MCP) server enabling AI agents (like Claude and Gemini) to search the system constitution, pull requirements, and run self-checks.
-   **`/github-action`**: Pull Request pipeline validator that blocks non-compliant merges.

---

## 🔍 Axiom Verification Matrix

First-ADE enforces compliance against the system's core axioms and postulates:

| Postulate | Target Principle | Enforcement Action |
| :--- | :--- | :--- |
| **Π.1.1** | Specification Existence | Verifies that a spec file exists for all staged changes (Speckit standard). |
| **Π.2.1** | Test-First Alignment | Enforces that matching unit or integration tests exist before code is implemented. |
| **Π.3.1** | Traceability Links | Extracts AST comment links (`implements:`, `traces_to:`) across Python, JS, TS, and Java. |
| **Π.4.1** | Architectural Constraints | Statically checks dependency boundaries and imports using `import-linter`. |
| **Π.5.3** | Agent Self-Governance | Detects repeated agent failures, escalating to a Human Architect after 3 failed runs. |

---

## 🛡️ Git-Based Human Overrides (No SaaS Required)

Authorized Human Architects can register temporary or permanent compliance exceptions (overrides) directly in `.ade-compliance.yml`. Overrides are checked in, reviewed in Pull Requests, and signed cryptographically:

```yaml
overrides:
  - id: "ovr-89a3f2"
    axiom_id: "Π.1.1"
    scope_type: "FILE"
    scope_value: "src/legacy_module.py"
    rationale: "Legacy module requires restructuring before spec integration."
    created_by: "HA-01"
    expires_at: "2026-09-01"
    signature: "SSO-SIG-b64..."
```

---

## 🚀 Quickstart Guide

### 1. Installation

Bootstrap the virtual environment and install the CLI:

```powershell
uv venv
source .venv/bin/activate
uv pip install -e "./cli[dev]"
```

### 2. Run Local Compliance Check

```powershell
# Run all compliance engines concurrently on specified files
ade-compliance check-all src/

# Run specification-only audit
ade-compliance check-spec src/

# Run test-first checks
ade-compliance check-test src/

# Run traceability matrix extraction
ade-compliance check-traceability src/
```

### 3. Registering an Override

Register an exception bypass directly from the command line:

```powershell
ade-compliance override Π.1.1 \
  --scope-value "src/legacy/" \
  --scope-type "DIRECTORY" \
  --rationale "Legacy codebase migration; exceptions validated by architect." \
  --created-by "HA-01" \
  --expires-in-days 30
```

---

## 🧪 Development & Verification

To run tests, run Ruff format checks, and execute strict type validation:

```powershell
# Format and Lint
uv run ruff format .
uv run ruff check .

# Type-check
uv run mypy cli/

# Run Test Suite
uv run pytest
```

---

*Building on first principles, one axiom at a time.*
