# Implementation Plan: ADE Compliance Framework

**Branch**: `001-ade-compliance` | **Date**: 2026-02-06 | **Spec**: [spec.md](file:///c:/Users/bfoxt/first-ade/specs/001-ade-compliance/spec.md)
**Input**: Feature specification from `/specs/001-ade-compliance/spec.md`

## Summary

Agentic-first compliance enforcement framework for Axiom Driven Engineering. Implements pre-commit/pre-push gates, specification-first and test-first validation, traceability extraction across 4 languages (Python, TS, JS, Java), Human Architect escalation via GitHub, immutable audit trail, agent self-governance with attestation, and a CLI/HTTP API surface. Python 3.11+ core with Tree-sitter for multi-language parsing.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Tree-sitter (multi-lang parsing), Click (CLI), FastAPI (HTTP API), Pydantic (data models), SQLAlchemy (audit persistence)
**Storage**: SQLite (local audit trail, low volume — hundreds/day); JSON config files
**Testing**: pytest with pytest-cov, hypothesis (property-based), pytest-asyncio
**Target Platform**: Local developer machine (CLI + pre-commit hook); HTTP API for agent integration
**Project Type**: Single project — CLI tool + local HTTP server
**Performance Goals**: All checks <10s (SC-002); p95 <5s for single-file checks
**Constraints**: Fail-closed on internal failure; per-file serialization for audit consistency; 90-day default override expiration
**Scale/Scope**: Single-developer local use; hundreds of decisions/day; 4 programming languages for traceability

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| #   | Principle                  | Status | Evidence                                                                                         |
| --- | -------------------------- | ------ | ------------------------------------------------------------------------------------------------ |
| I   | Axiom Acceptance           | ✅ PASS | Spec maps all FRs to axiom references (Π.1.1, Π.2.1, Π.3.1, etc.)                                |
| II  | Specification Governance   | ✅ PASS | spec.md complete; plan.md (this file); tasks.md follows                                          |
| III | Deterministic Verification | ✅ PASS | FR-015 mandates test determinism; pytest with seeded RNG; no external I/O in unit tests          |
| IV  | Traceable Decision Records | ✅ PASS | ADR required for Tree-sitter selection, HTTP→MCP migration, fail-closed policy (see research.md) |
| V   | Architectural Constraints  | ✅ PASS | Single-direction dependency flow: CLI → Services → Engines → Models; no circular deps            |
| VI  | AI Collaboration           | ✅ PASS | Agent context files maintained; FR-013/014 enforce agent self-check + attestation                |
| VII | Coverage Requirements      | ✅ PASS | SC-007 mandates ≥80% core coverage; FR-016 enforces configurable thresholds                      |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-ade-compliance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── compliance-api.yaml
└── tasks.md             # Phase 2 output (by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── ade_compliance/
│   ├── __init__.py
│   ├── cli.py                 # Click CLI entry point
│   ├── server.py              # FastAPI HTTP API for agents
│   ├── config.py              # YAML config loader + defaults
│   ├── models/
│   │   ├── __init__.py
│   │   ├── axiom.py           # Axiom, Violation, TraceLink entities
│   │   ├── decision.py        # Decision, Override, Attestation entities
│   │   └── report.py          # ComplianceReport schema
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── spec_engine.py     # Specification-first validation (FR-001, FR-004)
│   │   ├── test_engine.py     # Test-first validation (FR-002, FR-015, FR-016)
│   │   ├── trace_engine.py    # Traceability validation (FR-003, FR-020)
│   │   ├── adr_engine.py      # ADR detection (FR-005)
│   │   └── base.py            # Abstract engine interface
│   ├── services/
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # Check orchestration + per-file serialization (FR-030)
│   │   ├── escalation.py      # GitHub integration + local queue (FR-008, FR-009, FR-028)
│   │   ├── audit.py           # Immutable audit trail (FR-007)
│   │   ├── override.py        # Override lifecycle (FR-021, FR-029)
│   │   └── attestation.py     # Agent attestation service (FR-013, FR-014)
│   ├── hooks/
│   │   ├── __init__.py
│   │   └── pre_commit.py      # Git pre-commit hook (FR-010)
│   └── observability/
│       ├── __init__.py
│       └── metrics.py         # Prometheus-style metrics (FR-026)
│
├── pyproject.toml
└── .ade-compliance.yml        # Default config example

tests/
├── unit/
│   ├── engines/
│   │   ├── test_spec_engine.py
│   │   ├── test_test_engine.py
│   │   ├── test_trace_engine.py
│   │   └── test_adr_engine.py
│   ├── services/
│   │   ├── test_orchestrator.py
│   │   ├── test_escalation.py
│   │   ├── test_audit.py
│   │   ├── test_override.py
│   │   └── test_attestation.py
│   └── models/
│       └── test_models.py
├── integration/
│   ├── test_pre_commit_hook.py
│   ├── test_cli.py
│   └── test_server.py
└── conftest.py
```

**Structure Decision**: Single project with clear layered architecture. CLI and HTTP server are thin entry points delegating to services, which orchestrate engines. Models are pure data structures with no I/O. This matches Constitutional Principle V (single responsibility, one-direction dependency flow).

## Complexity Tracking

> No violations requiring justification. All constitutional gates pass.
