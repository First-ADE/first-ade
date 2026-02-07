<!-- Sync Impact Report
  Version change: 0.0.0 (unpopulated template) → 1.0.0 (initial population)
  Modified principles: N/A (initial population from template placeholders)
  Added sections:
    - 7 Principles mapped from docs/CONSTITUTION.md Articles 0–VI
    - Quality Gates section (Article VI)
    - Development Workflow section (Article I §1.3)
    - Governance section (Article VII)
  Removed sections: None
  Templates status:
    - .specify/templates/plan-template.md    ✅ aligned (Constitution Check gate present at L30-34)
    - .specify/templates/spec-template.md    ✅ aligned (user scenarios + acceptance criteria match §1.2/§2.1)
    - .specify/templates/tasks-template.md   ✅ aligned (test-first phasing matches §2.1; story-based structure matches §1.3)
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
Architectural decisions MUST be recorded in ADRs using the MADR format with ADE extensions (Governing Postulate and Axiom Traceability fields). ADRs are required for new components, technology selections, breaking API changes, and security-sensitive changes. ADRs progress through: Proposed → Accepted → Deprecated | Superseded.

### V. Architectural Constraints *(Σ.4, Π.4.1, Π.4.1a, Π.4.1b)*
Components MUST have a single reason to change. Dependencies MUST flow in one direction (UI → Application → Domain → Infrastructure); circular dependencies are prohibited. Interfaces MUST expose minimal surface area. Breaking interface changes require ADRs.

### VI. AI Collaboration *(Σ.5, Π.5.1, Π.5.2, Π.5.2a)*
Repositories MUST provide AI context files: `copilot-instructions.md`, `.gemini.md`, `.claude.md`, and `.specify/memory/constitution.md`. AI agents MUST operate within constitutional constraints, MUST NOT bypass quality gates, MUST escalate after 3 failed strategies (Π.5.3), and MUST produce verification artifacts (screenshots for UI, test output for logic, diff summaries for refactoring).

### VII. Coverage Requirements *(Σ.2, Π.2.1)*
Core business logic MUST maintain ≥80% line coverage. API endpoints MUST have 100% happy-path coverage. Utility functions MUST maintain ≥70% coverage.

## Quality Gates

All PRs MUST pass the following gates before merge:

| Gate     | Tool           | Threshold     |
| -------- | -------------- | ------------- |
| Tests    | pytest/vitest  | 100% pass     |
| Coverage | coverage.py/c8 | ≥80% (core)   |
| Types    | mypy/tsc       | strict mode   |
| Lint     | ruff/eslint    | zero errors   |
| Secrets  | detect-secrets | zero findings |

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

1. Propose amendment via ADR
2. Reference the violated or evolved axiom/postulate
3. Team review period (minimum 3 days)
4. Ratification by project lead

All PRs and reviews MUST verify constitutional compliance. Complexity MUST be justified via the Complexity Tracking table in `plan.md`. Use `.gemini.md`, `.claude.md`, and `copilot-instructions.md` for runtime development guidance.

**Version**: 1.0.0 | **Ratified**: 2026-02-06 | **Last Amended**: 2026-02-06
