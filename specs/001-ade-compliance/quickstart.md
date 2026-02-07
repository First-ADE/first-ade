# Quickstart: ADE Compliance Framework

**Phase**: 1 — Design & Contracts
**Date**: 2026-02-06

## Prerequisites

- Python 3.11+
- Git repository with `.ade-compliance.yml` (optional — sensible defaults apply)
- `pip` or `uv` for package installation

## Install

```bash
pip install ade-compliance
# or
uv pip install ade-compliance
```

## Setup Pre-Commit Hook

```bash
ade-compliance install-hook
# Installs git pre-commit hook that runs compliance checks automatically
```

## Configuration (.ade-compliance.yml)

Create in repo root (optional):

```yaml
version: "1.0"
strictness:
  default: enforce        # audit | warn | enforce
  overrides:
    Π.3.1: warn           # relax traceability for legacy code
coverage:
  threshold: 80
escalation:
  github_repo: "org/repo"
```

Without config, the framework uses `enforce` mode with 80% coverage threshold.

## CLI Usage

```bash
# Run all checks
ade-compliance check-all

# Run specific checks
ade-compliance check-spec
ade-compliance check-test
ade-compliance check-traceability

# Generate JSON report
ade-compliance generate-report --output report.json

# Override a violation (Human Architect only)
ade-compliance override --axiom Π.3.1 --scope src/legacy/ --rationale "Legacy module, migrating incrementally"
```

## HTTP API (Agent Integration)

```bash
# Start the local compliance server
ade-compliance serve
# → http://127.0.0.1:8420

# Agent runs a check
curl -X POST http://127.0.0.1:8420/check \
  -H "Content-Type: application/json" \
  -d '{"paths": ["src/feature/"], "agent_id": "gemini-2.5-pro"}'

# Agent submits attestation
curl -X POST http://127.0.0.1:8420/attest \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "gemini-2.5-pro", "task_ref": "abc123", "axioms_checked": ["Π.1.1", "Π.2.1"], "all_satisfied": true, "confidence_score": 0.95}'

# Prometheus metrics
curl http://127.0.0.1:8420/metrics
```

## Strictness Levels

| Level     | Behavior                                      | Use Case                               |
| --------- | --------------------------------------------- | -------------------------------------- |
| `audit`   | Log violations, no blocking                   | Initial adoption, baseline measurement |
| `warn`    | Display violations, allow with acknowledgment | Transitional period                    |
| `enforce` | Block non-compliant operations                | Production enforcement                 |

## Exit Codes

| Code | Meaning                                           |
| ---- | ------------------------------------------------- |
| 0    | All checks passed                                 |
| 1    | Violations found (enforce mode)                   |
| 2    | Warnings found (warn mode, non-blocking)          |
| 3    | Internal error (fail-closed — operations blocked) |
