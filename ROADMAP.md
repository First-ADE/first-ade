# First-ADE Open-Source Roadmap

This document outlines the public milestones, feature goals, and timeline for the First-ADE open-source project. First-ADE is transitioning into a **local-first, mathematically sound agentic verification gate**.

---

## 🗺️ Execution Timeline & Phases

```
┌────────────────────────────────────────────────────────┐
│ Phase 1: Stabilization & Quality Alignment (Immediate) │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 2: Git-Native Governance & Signatures (Q3 2026)  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 3: The Simulation & Proof Engine (Q4 2026)       │
└────────────────────────────────────────────────────────┘
```

---

## 🎯 Detailed Milestones

### Phase 1: Stabilization & Quality Alignment (Q2 2026)
*   **Goal**: Establish a 100% passing test suite and fix the legacy CLI configuration mismatches.
*   **Deliverables**:
    *   [ ] Fix Click command-line arguments to support standard developer options (`--scope-value`, `--rationale`) for overrides.
    *   [ ] Implement type-safe severity-to-criticality mappings directly in configuration modules.
    *   [ ] Set up clean pre-commit hooks that execute Ruff, Mypy, and Pytest concurrently.
    *   [ ] Standardize the Obsidian vault layout (`.obsidian-vault/`) and symbol links for local developer context sharing.

### Phase 2: Git-Native Governance (Q3 2026)
*   **Goal**: Move all authorization, overrides, and audit trails into local Git repositories, completely removing external databases.
*   **Deliverables**:
    *   [ ] Refactor override registration to write signed, version-controlled entries directly to `.ade-compliance.yml`.
    *   [ ] Add cryptographic OIDC key validation (enforcing that override creators are authorized Human Architects).
    *   [ ] Convert the audit trail from SQLite to Git commit metadata and JSON change-ledgers, enabling pull-request based audit reviews.
    *   [ ] Deprecate the REST API server (`serve` command) in favor of a 100% serverless workflow.

### Phase 3: The Simulation & Proof Engine (Q4 2026)
*   **Goal**: Build the core value-add features that enable agents to simulate execution states and prove specification constraints.
*   **Deliverables**:
    *   [ ] **State Simulation (Approach A)**: Provide a `@ade.trace_state` decorator to trace actual state mutations during testing, matching them against local JSON predictions.
    *   [ ] **Symbolic AST Proofs (Approach B)**: Integrate a Python AST analyzer with the Z3 SMT solver to statically prove logic contracts (e.g. input bounds, error conditions).
    *   [ ] **Self-Healing Compliance (Approach C)**: Add CLI repair tools that autogenerate traceability comments and test skeletons when compliance gates fail.
    *   [ ] **MCP Server Protocol**: Expose the specification database and pre-execution compliance gates directly to AI agents.

---

## 🤝 Community & Contributions

We invite contributions to all phases of the roadmap! Please see our [Contributing Guide](./CONTRIBUTING.md) to get started. 

*For questions or suggestions, open a GitHub Issue or reach out to the Human Architect team.*
