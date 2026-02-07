# Research: ADE Compliance Framework

**Phase**: 0 — Outline & Research
**Date**: 2026-02-06

## Technology Decisions

### 1. Multi-Language Parsing — Tree-sitter

**Decision**: Tree-sitter for AST parsing across Python, TypeScript, JavaScript, Java
**Rationale**: Mature incremental parser with consistent API across languages. Python bindings (`tree-sitter` + language grammars) allow uniform traceability extraction without language-specific parsers.
**Alternatives considered**:
- regex-based extraction — fragile, can't handle nested structures
- Language-specific ASTs (ast module, ts-morph, etc.) — requires 4 separate implementations

### 2. CLI Framework — Click

**Decision**: Click for CLI interface
**Rationale**: Mature, composable command groups, built-in help generation, testable via CliRunner. Standard Python CLI choice.
**Alternatives considered**:
- argparse — more boilerplate, weaker composability
- Typer — Click wrapper, adds unnecessary dependency layer

### 3. HTTP API — FastAPI

**Decision**: FastAPI for the local agent compliance interface
**Rationale**: Async support, automatic OpenAPI docs, Pydantic integration for request/response validation. Roadmap path toward MCP evolution.
**Alternatives considered**:
- Flask — synchronous by default, less native validation
- gRPC — heavier for local-only use case

### 4. Audit Persistence — SQLite

**Decision**: SQLite for local audit trail storage
**Rationale**: Zero-config, file-based, handles hundreds of writes/day easily. Append-only table design for immutability. No external DB dependency.
**Alternatives considered**:
- PostgreSQL — overkill for local single-user; requires external service
- JSON file append — no query capability; corruption risk on concurrent access

### 5. Fail-Closed Architecture

**Decision**: All internal failures block operations (fail-closed)
**Rationale**: Constitutional enforcement system cannot have exploitable gaps. A fail-open stance would allow non-compliant code through during outages.
**ADR required**: Yes — documents the security tradeoff and developer experience impact

### 6. Strictness Levels (Incremental Adoption)

**Decision**: Three levels — audit, warn, enforce — configurable per axiom
**Rationale**: Legacy codebases cannot adopt full enforcement immediately. Graduated adoption reduces friction while allowing measurable progress.
**ADR required**: Yes — documents the compliance tradeoff

### 7. Override Lifecycle

**Decision**: Mandatory scope + 90-day default expiration + auto-revert
**Rationale**: Prevents permanent compliance gaps from accumulating. Scoping limits blast radius. 7-day pre-expiry notification prevents surprise enforcement.

### 8. Escalation Resilience

**Decision**: Local queue with exponential backoff (5 retries / 15 min) when GitHub unreachable
**Rationale**: Network failures must not permanently block agent work. Bounded retry prevents infinite queuing. Agent block after retry exhaustion ensures Human Architect awareness.

## Dependency Best Practices

### Tree-sitter in Python
- Use `tree-sitter>=0.21` with pre-built language wheels (`tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript`, `tree-sitter-java`)
- Parse files lazily (only on check invocation, not at import time)
- Cache parsed ASTs per-file hash to avoid redundant parsing within a single check run

### FastAPI Local Server
- Bind to `127.0.0.1` only (no external access)
- Use `uvicorn` with `--workers 1` (serialization is per-file, not per-request)
- Health endpoint at `/health` for agent connectivity checks

### SQLite Audit Trail
- Append-only design: INSERT only, no UPDATE/DELETE
- WAL mode for concurrent read/write
- SHA-256 hash chain for tamper evidence (each row includes hash of previous row)

## Open Items

None — all NEEDS CLARIFICATION resolved via spec clarifications.
