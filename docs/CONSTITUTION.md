# ADE Constitution

**Governance Principles for Axiom Driven Engineering**

---

## Preamble

This Constitution establishes the governance framework for all projects operating under Axiom Driven Engineering principles. It derives its authority from the [Core Axioms](./AXIOMS.md) and their [Postulate derivations](./POSTULATES.md).

All constitutional principles include a traceability reference to their governing postulate(s).

---

## Article 0: Axiom Acceptance

### §0.1 Mandatory Acceptance
**Every participant, whether Human or LLM Agent, MUST read and explicitly accept the ADE Core Axioms before interacting with any project specification or code.** *(Σ.1, Σ.5)*

- Acceptance is a prerequisite for all development activity.
- Agents must acknowledge acceptance in their initial system prompt or session start.
- Failure to accept the axioms disqualifies the participant from contributing to or modifying the project.

---

## Article I: Specification Governance

*Derived from Σ.1 and Π.1.x postulates*

### §1.1 Specification Requirement
**No feature code shall be written without a corresponding specification.** *(Π.1.1)*

- Specifications reside in `.specify/specs/{feature-name}/`
- Required files: `spec.md` (requirements), `plan.md` (architecture), `tasks.md` (work breakdown)
- Violations block PR merge

### §1.2 Specification Format
**Specifications shall follow the Spec-Kit format.** *(Π.1.2a)*

```
spec.md   — User stories, acceptance criteria, functional requirements
plan.md   — Technical design, component diagrams, API contracts
tasks.md  — Atomic implementation tasks with dependencies
```

### §1.3 Specification Workflow
**The Spec-Kit lifecycle shall govern all feature development.** *(Π.1.3)*

1. `specify` — Define requirements
2. `clarify` — Resolve ambiguities
3. `plan` — Design architecture
4. `tasks` — Create work breakdown
5. `implement` — Execute tasks
6. `analyze` — Post-implementation review

---

## Article II: Verification Standards

*Derived from Σ.2 and Π.2.x postulates*

### §2.1 Test-First Development
**All features shall have failing tests before implementation.** *(Π.2.1)*

- The RED commit precedes the GREEN commit
- Commits without test coverage require justification

### §2.2 Determinism Requirements
**Tests shall be deterministic and isolated.** *(Π.2.1a)*

- No external network calls in unit tests
- Mock all I/O and external services
- Seed all random number generators
- Avoid `sleep()` for timing; use deterministic waits

### §2.3 Performance Constraints
**Test suites shall complete in bounded time.** *(Π.2.3a)*

| Test Type         | Maximum Duration |
| ----------------- | ---------------- |
| Unit suite        | 60 seconds       |
| Integration suite | 5 minutes        |
| E2E suite         | 15 minutes       |

### §2.4 Coverage Requirements
**Core logic shall maintain minimum coverage.** *(Π.2.1)*

- Core business logic: ≥80% line coverage
- API endpoints: 100% happy-path coverage
- Utility functions: ≥70% coverage

---

## Article III: Decision Records

*Derived from Σ.3 and Π.3.x postulates*

### §3.1 ADR Requirement
**Architectural decisions shall be recorded in ADRs.** *(Π.3.1)*

Required for:
- New components or services
- Technology selections
- Breaking API changes
- Security-sensitive changes

### §3.2 ADR Format
**ADRs shall follow the MADR format with ADE extensions.** *(Π.3.2)*

Required sections:
```markdown
# ADR-{NUMBER}: {TITLE}
## Status
## Governing Postulate    ← ADE Extension
## Context
## Decision
## Consequences
## Axiom Traceability     ← ADE Extension
```

### §3.3 ADR Lifecycle
**ADRs progress through defined states.** *(Π.3.1)*

```
Proposed → Accepted → [Deprecated | Superseded]
```

- Proposed ADRs require team review
- Accepted ADRs are immutable (create new ADR to change)
- Superseded ADRs link to their replacement

---

## Article IV: Architectural Constraints

*Derived from Σ.4 and Π.4.x postulates*

### §4.1 Single Responsibility
**Components shall have one reason to change.** *(Π.4.1)*

- One public class/function per responsibility
- Services expose focused APIs
- Utilities are pure functions where possible

### §4.2 Dependency Direction
**Dependencies shall flow in one direction.** *(Π.4.1a)*

```
UI → Application → Domain → Infrastructure
       ↑              ↑
    No reverse flow allowed
```

- Circular dependencies are prohibited
- Dependency injection for cross-layer communication

### §4.3 Interface Minimalism
**Interfaces shall expose minimal surface area.** *(Π.4.1b)*

- Prefer fewer, well-defined methods over many specialized ones
- Internal implementation details remain private
- Breaking interface changes require ADRs

---

## Article V: AI Collaboration

*Derived from Σ.5 and Π.5.x postulates*

### §5.1 Context Files
**Repositories shall provide AI context files.** *(Π.5.1, Π.5.2)*

| File                              | Purpose                                |
| --------------------------------- | -------------------------------------- |
| `copilot-instructions.md`         | GitHub Copilot guidance                |
| `.gemini.md`                      | Google Gemini/Antigravity guidance     |
| `.claude.md`                      | Anthropic Claude guidance              |
| `.specify/memory/constitution.md` | Project-specific constitutional subset |

### §5.2 Agent Constraints
**AI agents shall operate within defined boundaries.** *(Π.5.1a)*

- Agents follow project constitution
- Agents do not bypass quality gates
- Agents escalate after 3 failed strategies (Π.5.3)
- Agent-generated code requires human review

### §5.3 Verification Artifacts
**AI work shall produce verification evidence.** *(Π.5.1b)*

- Screenshots for UI changes
- Test output for logic changes
- Diff summaries for refactoring

---

## Article VI: Quality Gates

### §6.1 Pre-Merge Requirements

All PRs must pass:

| Gate     | Tool           | Threshold     |
| -------- | -------------- | ------------- |
| Tests    | pytest/vitest  | 100% pass     |
| Coverage | coverage.py/c8 | ≥80% (core)   |
| Types    | mypy/tsc       | strict mode   |
| Lint     | ruff/eslint    | zero errors   |
| Secrets  | detect-secrets | zero findings |

### §6.2 Branch Protection

The `main` branch shall:
- Require PR reviews (minimum 1)
- Require status checks to pass
- Prohibit direct pushes
- Require linear history (squash or rebase)

---

## Article VII: Amendments

### §7.1 Amendment Process

1. Propose amendment via ADR
2. Reference violated or evolved axiom/postulate
3. Team review period (minimum 3 days)
4. Ratification by project lead

### §7.2 Versioning

- MAJOR: Axiom changes
- MINOR: Postulate additions
- PATCH: Clarifications and typo fixes

---

**Version**: 1.0.0 | **Ratified**: 2026-02-06 | **Authority**: Derived from ADE Axioms v1.0.0
