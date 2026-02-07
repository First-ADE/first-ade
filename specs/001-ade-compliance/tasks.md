# Tasks: ADE Compliance Framework

**Input**: Design documents from `/specs/001-ade-compliance/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Constitution Principle III mandates Red-Green-Refactor. Test tasks included per user story.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/ade_compliance/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and tooling

- [x] T001 Create project structure per plan.md layout (src/ade_compliance/, tests/unit/, tests/integration/)
- [x] T002 Initialize Python 3.11+ project with pyproject.toml (click, fastapi, pydantic, sqlalchemy, tree-sitter, pyadr, pytest, hypothesis)
- [x] T003 [P] Configure linting (ruff), formatting (ruff format), and type checking (mypy strict) in pyproject.toml
- [x] T004 [P] Create default .ade-compliance.yml config file at repo root
- [x] T005 Initialize ADR repository via `pyadr init` in docs/decisions/
- [x] T006 [P] Create ADR for Tree-sitter selection via `pyadr propose "Use Tree-sitter for multi-language parsing"`
- [x] T007 [P] Create ADR for fail-closed architecture via `pyadr propose "Fail-closed architecture for compliance enforcement"`
- [x] T008 [P] Create ADR for strictness levels via `pyadr propose "Three strictness levels for incremental adoption"`
- [x] T009 [P] Create ADR for SQLite audit trail via `pyadr propose "SQLite for local audit trail"`
- [x] T010 [P] Create ADR for local HTTP API via `pyadr propose "Local HTTP API evolving to MCP"`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, config loader, base engine interface, and audit infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundation

- [x] T011 [P] Unit tests for Axiom model in tests/unit/models/test_models.py
- [x] T012 [P] Unit tests for Violation model (state transitions) in tests/unit/models/test_models.py
- [x] T013 [P] Unit tests for config loader in tests/unit/test_config.py

### Implementation for Foundation

- [x] T014 [P] Implement Axiom model (id, name, category, severity, enabled) in src/ade_compliance/models/axiom.py
- [x] T015 [P] Implement Violation model with state machine (NEW→ACKNOWLEDGED→RESOLVED|OVERRIDDEN) in src/ade_compliance/models/axiom.py
- [x] T016 [P] Implement TraceLink model in src/ade_compliance/models/axiom.py
- [x] T017 [P] Implement Decision model with criticality routing in src/ade_compliance/models/decision.py
- [x] T018 [P] Implement Override model with expiration and scope in src/ade_compliance/models/decision.py
- [x] T019 [P] Implement Attestation model with confidence threshold in src/ade_compliance/models/decision.py
- [x] T020 [P] Implement ComplianceReport schema in src/ade_compliance/models/report.py
- [x] T021 Implement YAML config loader with defaults in src/ade_compliance/config.py
- [x] T022 Implement abstract base engine interface in src/ade_compliance/engines/base.py
- [x] T023 Implement SQLite audit trail service (append-only, WAL, SHA-256 hash chain) in src/ade_compliance/services/audit.py
- [x] T024 Unit tests for audit service in tests/unit/services/test_audit.py

**Checkpoint**: Foundation ready — all models, config, base engine, and audit trail operational

---

## Phase 3: User Story 2 — Specification-First Enforcement (Priority: P1) 🎯 MVP

**Goal**: Verify specs exist before implementation begins (Π.1.1) — FR-001, FR-004

**Independent Test**: Run `ade-compliance check-spec` against a repo with/without spec files → blocked or approved

### Tests for US-2

- [x] T025 [P] [US2] Unit tests for spec engine (no spec → reject, valid spec → approve, wrong format → feedback) in tests/unit/engines/test_spec_engine.py

### Implementation for US-2

- [x] T026 [US2] Implement spec engine: detect spec existence, validate format (EARS patterns) in src/ade_compliance/engines/spec_engine.py
- [x] T027 [US2] Add spec engine violation reporting with Π.1.1 references and remediation guidance in src/ade_compliance/engines/spec_engine.py

**Checkpoint**: Spec-first validation independently functional

---

## Phase 4: User Story 3 — Test-First Enforcement (Priority: P1)

**Goal**: Verify tests exist before implementation code creation (Π.2.1) — FR-002, FR-015, FR-016

**Independent Test**: Stage code with/without corresponding test file → blocked or approved

### Tests for US-3

- [x] T028 [P] [US3] Unit tests for test engine (no test → block, insufficient coverage → flag, adequate → allow) in tests/unit/engines/test_test_engine.py

### Implementation for US-3

- [x] T029 [US3] Implement test engine: detect test file existence, check test determinism (no external I/O, no sleep) in src/ade_compliance/engines/test_engine.py
- [x] T030 [US3] Add configurable coverage threshold enforcement (default 80%, strictness: warn) in src/ade_compliance/engines/test_engine.py

**Checkpoint**: Test-first validation independently functional

---

## Phase 5: User Story 1 — Compliance Gate at Commit Time (Priority: P1)

**Goal**: Pre-commit hook runs all checks automatically — FR-010, FR-006, FR-025, FR-030

**Independent Test**: Stage non-compliant code → commit blocked with violation report; stage compliant code → commit succeeds

**Depends on**: US-2 (spec engine), US-3 (test engine)

### Tests for US-1

- [x] T031 [P] [US1] Unit tests for orchestrator (parallel engine dispatch, per-file serialization) in tests/unit/services/test_orchestrator.py
- [ ] T032 [P] [US1] Integration test for pre-commit hook in tests/integration/test_pre_commit_hook.py

### Implementation for US-1

- [x] T033 [US1] Implement orchestrator service: dispatch to engines, aggregate results, per-file serialization (FR-030) in src/ade_compliance/services/orchestrator.py
- [x] T034 [US1] Implement fail-closed error handling in orchestrator (FR-025) in src/ade_compliance/services/orchestrator.py
- [ ] T035 [US1] Implement git pre-commit hook integration in src/ade_compliance/hooks/pre_commit.py
- [ ] T036 [US1] Add `install-hook` CLI command to register pre-commit hook in src/ade_compliance/cli.py

**Checkpoint**: Pre-commit gate blocks non-compliant commits with detailed reports

---

## Phase 6: User Story 8 — Agent Self-Governance and Attestation (Priority: P1 - Promoted)

**Note**: Promoted to P1 to enable agent self-correction before commit.

**Goal**: Agent pre-execution self-check and post-task attestation — FR-013, FR-014, FR-017, FR-018

**Independent Test**: POST /check → compliance results; POST /attest → attestation recorded; low confidence → escalation

### Tests for US-8

- [ ] T059 [P] [US8] Unit tests for attestation service (record, confidence threshold, escalation trigger) in tests/unit/services/test_attestation.py
- [ ] T060 [P] [US8] Integration test for HTTP API endpoints in tests/integration/test_server.py

### Implementation for US-8

- [ ] T061 [US8] Implement attestation service (record attestation, confidence < 0.7 → escalate) in src/ade_compliance/services/attestation.py
- [ ] T062 [US8] Implement FastAPI server with health, check, attest endpoints in src/ade_compliance/server.py
- [ ] T063 [US8] Implement reports and overrides endpoints in src/ade_compliance/server.py
- [ ] T064 [US8] Implement Prometheus-compatible /metrics endpoint (FR-026) in src/ade_compliance/observability/metrics.py
- [ ] T065 [US8] Add `serve` command to CLI in src/ade_compliance/cli.py
- [ ] T066 [US8] Bind server to 127.0.0.1 only with uvicorn single-worker in src/ade_compliance/server.py

**Checkpoint**: Agent HTTP API functional for self-check, attestation, and observability

---

## Phase 7: User Story 4 — Traceability Validation (Priority: P2)

**Goal**: Validate traceability links across 4 languages using Tree-sitter — FR-003, FR-019, FR-020

**Independent Test**: Run traceability check on code with/without markers → pass/fail with matrix output

### Tests for US-4

- [ ] T037 [P] [US4] Unit tests for trace engine (markers present → pass, missing → fail, matrix generation) in tests/unit/engines/test_trace_engine.py

### Implementation for US-4

- [ ] T038 [US4] Implement Tree-sitter parser wrappers for Python, TypeScript, JavaScript, Java in src/ade_compliance/engines/trace_engine.py
- [ ] T039 [US4] Implement traceability link extraction from AST (comments, decorators, docstrings) in src/ade_compliance/engines/trace_engine.py
- [ ] T040 [US4] Implement traceability matrix generation (code→tests→requirements→axioms) in src/ade_compliance/engines/trace_engine.py
- [ ] T041 [US4] Add AST cache by file hash for performance in src/ade_compliance/engines/trace_engine.py

**Checkpoint**: Traceability validation works independently across 4 languages

---

## Phase 8: User Story 5 — Human Architect Escalation (Priority: P2)

**Goal**: Auto-route critical decisions to Human Architect via GitHub — FR-008, FR-009, FR-022, FR-028

**Independent Test**: Trigger high-criticality decision → GitHub issue created; trigger 3 failures → escalation with context

### Tests for US-5

- [ ] T042 [P] [US5] Unit tests for escalation service (criticality routing, 3-failure escalation, local queue retry) in tests/unit/services/test_escalation.py

### Implementation for US-5

- [ ] T043 [US5] Implement escalation service: criticality classification (low/med auto-approve, high/critical → escalate) in src/ade_compliance/services/escalation.py
- [ ] T044 [US5] Implement 3-failure escalation trigger (Π.5.3) with full context packaging in src/ade_compliance/services/escalation.py
- [ ] T045 [US5] Implement GitHub integration (create issues, PR comments) in src/ade_compliance/services/escalation.py
- [ ] T046 [US5] Implement local queue with exponential backoff (5 retries / 15 min) for GitHub failures in src/ade_compliance/services/escalation.py
- [ ] T047 [US5] Implement Human Architect review rate tracking (<5% threshold, FR-022) in src/ade_compliance/services/escalation.py

**Checkpoint**: Escalation service routes decisions correctly with GitHub resilience

---

## Phase 9: User Story 6 — Audit Trail and Reporting (Priority: P2)

**Goal**: Immutable audit trail with reporting — FR-007, FR-012, FR-024

**Independent Test**: Run compliance checks → verify audit entries logged with hash chain; generate trend report

### Tests for US-6

- [ ] T048 [P] [US6] Unit tests for compliance report generation (JSON schema, metrics) in tests/unit/models/test_report.py

### Implementation for US-6

- [ ] T049 [US6] Implement compliance report generation with schema versioning in src/ade_compliance/services/audit.py
- [ ] T050 [US6] Implement 30-day trend report (violation counts, severity distributions) in src/ade_compliance/services/audit.py
- [ ] T051 [US6] Implement override audit logging (rule, rationale, timestamp, affected components) in src/ade_compliance/services/override.py
- [ ] T052 [US6] Unit tests for override service in tests/unit/services/test_override.py

**Checkpoint**: Audit trail captures all decisions with tamper-evident hash chain

---

## Phase 10: User Story 7 — CLI for Manual Checks (Priority: P3)

**Goal**: Developer-facing CLI for compliance checks — FR-011, FR-012

**Independent Test**: Run `ade-compliance check-all` on a repo → compliance report output; run `ade-compliance check-traceability` → traceability matrix; run `ade-compliance generate-report` → JSON report

**Depends on**: US-1 (orchestrator), US-2 (spec engine), US-3 (test engine)

### Tests for US-7

- [ ] T053 [P] [US7] Unit tests for CLI check-all command output formatting in tests/unit/test_cli.py
- [ ] T054 [P] [US7] Integration test for full CLI check-all workflow in tests/integration/test_cli_integration.py

### Implementation for US-7

- [ ] T055 [US7] Implement `check-all` CLI command dispatching to orchestrator in src/ade_compliance/cli.py
- [ ] T056 [US7] Implement `check-traceability` CLI command invoking trace engine in src/ade_compliance/cli.py
- [ ] T057 [US7] Implement `generate-report` CLI command producing JSON compliance report in src/ade_compliance/cli.py
- [ ] T058 [US7] Add CLI exit code semantics (0=pass, 1=violations, 2=internal error) in src/ade_compliance/cli.py

**Checkpoint**: CLI provides developer-facing manual compliance check interface

---

## Phase 11: ADR Detection Engine

**Purpose**: FR-005 — cross-cutting concern used by orchestrator

- [ ] T067 [P] Unit tests for ADR engine in tests/unit/engines/test_adr_engine.py
- [ ] T068 Implement ADR engine: detect architectural changes, verify ADR exists via `pyadr check-adr-repo` in src/ade_compliance/engines/adr_engine.py
- [ ] T069 Register ADR engine in orchestrator dispatch in src/ade_compliance/services/orchestrator.py

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

- [ ] T070 [P] Add override expiration auto-revert with 7-day pre-notification in src/ade_compliance/services/override.py
- [ ] T071 [P] Add strictness level support (audit/warn/enforce per axiom) across all engines in src/ade_compliance/config.py
- [ ] T072 [P] Documentation: update README.md with quickstart, architecture overview
- [ ] T073 [P] Add structured logging across all services in src/ade_compliance/observability/metrics.py
- [ ] T074 Security hardening: SSO validation for override/escalation endpoints in src/ade_compliance/server.py
- [ ] T075 Performance optimization: verify all checks complete <10s (SC-002)
- [ ] T076 Run `pyadr check-adr-repo` to validate all ADRs in docs/decisions/
- [ ] T077 Run quickstart.md validation end-to-end
- [ ] T078 [P] Implement deployment gate: block deployments with unresolved critical/high violations (FR-023) in src/ade_compliance/services/orchestrator.py
- [ ] T079 [P] Create AI context files per Constitution VI: copilot-instructions.md, .gemini.md, .claude.md
- [ ] T080 [P] Configure detect-secrets baseline per Constitution quality gates in .pre-commit-config.yaml

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US-2 (Phase 3)**: Depends on Foundation — no other story deps (MVP candidate)
- **US-3 (Phase 4)**: Depends on Foundation — no other story deps
- **US-1 (Phase 5)**: Depends on US-2 + US-3 (needs spec + test engines)
- **US-8 (Phase 6)**: Depends on Foundation — promoted to P1 for agent self-governance
- **US-4 (Phase 7)**: Depends on Foundation — independent of US-1/2/3
- **US-5 (Phase 8)**: Depends on Foundation — independent
- **US-6 (Phase 9)**: Depends on Foundation (audit service from Phase 2)
- **US-7 (Phase 10)**: Depends on US-1/2/3 engines existing — thin CLI layer
- **ADR Engine (Phase 11)**: Can run after Foundation, in parallel with other stories
- **Polish (Phase 12)**: Depends on all desired stories being complete

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Constitution III)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks T003–T010 marked [P] can run in parallel
- All Foundation model tasks T014–T020 marked [P] can run in parallel
- US-2, US-3 can start in parallel after Foundation (both P1, no interdependency)
- US-4, US-5, US-6 can start in parallel after Foundation (all P2, independent)
- ADR Engine (Phase 11) can run in parallel with any story after Foundation
- Tests within a story marked [P] can run in parallel

---

## Parallel Example: Foundation Models

```bash
# Launch all model tasks together (no interdependencies):
Task T014: "Implement Axiom model in src/ade_compliance/models/axiom.py"
Task T015: "Implement Violation model in src/ade_compliance/models/axiom.py"
Task T016: "Implement TraceLink model in src/ade_compliance/models/axiom.py"
Task T017: "Implement Decision model in src/ade_compliance/models/decision.py"
Task T018: "Implement Override model in src/ade_compliance/models/decision.py"
Task T019: "Implement Attestation model in src/ade_compliance/models/decision.py"
Task T020: "Implement ComplianceReport schema in src/ade_compliance/models/report.py"
```

## Parallel Example: P1 Stories After Foundation

```bash
# US-2 and US-3 can start simultaneously:
Developer A: Phase 3 (US-2: Spec-First Enforcement)
Developer B: Phase 4 (US-3: Test-First Enforcement)
# US-1 starts after both complete (needs both engines)
```

---

## Implementation Strategy

### MVP First (US-2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US-2 (Spec-First Enforcement)
4. **STOP and VALIDATE**: Test US-2 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundation → Foundation ready
2. US-2 + US-3 → Core enforcement engines (P1 MVP!)
3. US-1 → Pre-commit gate wired up (full P1 delivery)
4. US-4 + US-5 + US-6 → Traceability + Escalation + Audit (P2 delivery)
5. US-7 + US-8 → CLI + Agent API (P3 delivery)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundation together
2. Once Foundation is done:
   - Developer A: US-2 (Spec-First) → US-1 (Commit Gate)
   - Developer B: US-3 (Test-First) → US-4 (Traceability)
   - Developer C: US-5 (Escalation) → US-6 (Audit)
3. After P1+P2: US-7 + US-8 can be assigned independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (Constitution Principle III)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All ADRs MUST be created via `pyadr` CLI — never manually (Constitution Principle IV)
