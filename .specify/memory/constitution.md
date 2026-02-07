<!-- Sync Impact Report
  Version change: 1.1.0 → 1.1.1 (PATCH — added mandatory environment isolation)
  Modified principles:
    - V. Architectural Constraints: Added mandatory virtual environment requirement (no raw pip)
  Added sections: None
  Removed sections: None
  Templates status:
    - .specify/templates/plan-template.md    ✅ aligned
    - .specify/templates/spec-template.md    ✅ aligned
    - .specify/templates/tasks-template.md   ✅ aligned
  Follow-up TODOs: None
-->

# ADE Project Constitution

## Core Principles

### I. Axiom Acceptance *(Σ.1, Σ.5)*
Every participant—Human or LLM Agent—MUST read and explicitly accept the ADE Core Axioms before interacting with any project specification or code. Acceptance is a prerequisite for all development activity. Agents MUST acknowledge acceptance in their initial system prompt or session start. Failure to accept the axioms disqualifies the participant from contributing to or modifying the project.

### II. Specification Governance *(Σ.1, Π.1.1, Π.1.2, Π.1.2a)*
No feature code shall be written without a corresponding specification. Specifications reside in `.specify/specs/{feature-name}/` and MUST include `spec.md` (requirements), `plan.md` (architecture), and `tasks.md` (work breakdown). Violations block PR merge. Specifications MUST follow the Spec-Kit format.

### III. Deterministic Verification *(Σ.2, Π.2.1, Π.2.1a, Π.2.3a)*
All features MUST have failing tests before implementation (Red-Green-Refactor). Tests MUST be deterministic and isolated: no external network calls in unit tests, all I/O and external services mocked, all RNGs seeded, no `sleep()`-based timing. Unit suites MUST complete within 60 seconds; integration suites within 5 minutes; E2E suites within 15 minutes.

### IV. Traceable Decision Records *(Σ.3, Π.3.1, Π.3.2, Π.3.2a)*
Architectural decisions MUST be recorded in ADRs using the MADR format with ADE extensions (Governing Postulate and Axiom Traceability fields). ADRs MUST be created and managed exclusively via the `pyadr` CLI tool ([adr.github.io](https://adr.github.io/adr-tooling/)). Manual creation or inference of ADR files is PROHIBITED. ADRs are required for new components, technology selections, breaking API changes, and security-sensitive changes. ADRs progress through: Proposed → Accepted → Deprecated | Superseded.

**Mandatory ADR CLI commands** (via `pyadr` / `git adr`):
- `pyadr init` — Initialize ADR repository with MADR template
- `pyadr propose "<title>"` — Create new ADR in Proposed status
- `pyadr accept <path>` — Accept a proposed ADR
- `pyadr reject <path>` — Reject a proposed ADR
- `pyadr toc` — Regenerate ADR table of contents
- `pyadr check-adr-repo` — Validate ADR repository integrity
- `git adr propose|accept|reject` — Git-integrated variants (auto-branch, auto-stage)

### V. Architectural Constraints *(Σ.4, Π.4.1, Π.4.1a, Π.4.1b)*
Components MUST have a single reason to change. Dependencies MUST flow in one direction (UI → Application → Domain → Infrastructure); circular dependencies are prohibited. Interfaces MUST expose minimal surface area. Breaking interface changes require ADRs.

**Environment Isolation**: All Python projects MUST use isolated environments (`virtualenv`, `uv`, or `pipenv`). Installing packages globally or via raw `pip` without an active virtual environment is PROHIBITED.

### VI. AI Collaboration *(Σ.5, Π.5.1, Π.5.2, Π.5.2a)*
Repositories MUST provide AI context files: `copilot-instructions.md`, `.gemini.md`, `.claude.md`, and `.specify/memory/constitution.md`. AI agents MUST operate within constitutional constraints, MUST NOT bypass quality gates, MUST escalate after 3 failed strategies (Π.5.3), and MUST produce verification artifacts (screenshots for UI, test output for logic, diff summaries for refactoring).

### VII. Coverage Requirements *(Σ.2, Π.2.1)*
Core business logic MUST maintain ≥80% line coverage. API endpoints MUST have 100% happy-path coverage. Utility functions MUST maintain ≥70% coverage.

## Quality Gates

All PRs MUST pass the following gates before merge:

| Gate     | Tool                 | Threshold     |
| -------- | -------------------- | ------------- |
| Tests    | pytest/vitest        | 100% pass     |
| Coverage | coverage.py/c8       | ≥80% (core)   |
| Types    | mypy/tsc             | strict mode   |
| Lint     | ruff/eslint          | zero errors   |
| Secrets  | detect-secrets       | zero findings |
| ADRs     | pyadr check-adr-repo | zero errors   |

Branch protection for `main`: require PR reviews (minimum 1), require status checks to pass, prohibit direct pushes, require linear history (squash or rebase).

## Development Workflow

The Spec-Kit lifecycle governs all feature development:

1. `specify` — Define requirements
2. `clarify` — Resolve ambiguities
3. `plan` — Design architecture
4. `tasks` — Create work breakdown
5. `implement` — Execute tasks
6. `analyze` — Post-implementation review

## Governance

This constitution supersedes all other practices within the project scope. Amendments follow this process:

1. Propose amendment via ADR (`pyadr propose "Amend constitution: <description>"`)
2. Reference the violated or evolved axiom/postulate
3. Team review period (minimum 3 days)
4. Ratification by project lead

All PRs and reviews MUST verify constitutional compliance. Complexity MUST be justified via the Complexity Tracking table in `plan.md`. Use `.gemini.md`, `.claude.md`, and `copilot-instructions.md` for runtime development guidance.

**Version**: 1.1.1 | **Ratified**: 2026-02-06 | **Last Amended**: 2026-02-06
