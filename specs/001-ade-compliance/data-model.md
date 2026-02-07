# Data Model: ADE Compliance Framework

**Phase**: 1 — Design & Contracts
**Date**: 2026-02-06

## Entities

### Axiom

| Field            | Type   | Constraints                                                 |
| ---------------- | ------ | ----------------------------------------------------------- |
| id               | string | Primary key, format `Π.X.Y` or `Σ.X`                        |
| name             | string | Human-readable label                                        |
| category         | enum   | SPECIFICATION, TEST, TRACEABILITY, ARCHITECTURE, ESCALATION |
| description      | string | Full axiom text                                             |
| severity_default | enum   | low, medium, high, critical                                 |
| enabled          | bool   | Default true; toggled via config                            |

**Relationships**: Referenced by Violation, Decision, TraceLink, Override

---

### Violation

| Field       | Type     | Constraints                                  |
| ----------- | -------- | -------------------------------------------- |
| id          | uuid     | Primary key                                  |
| axiom_id    | string   | FK → Axiom.id                                |
| severity    | enum     | low, medium, high, critical                  |
| file_path   | string   | Relative to repo root                        |
| line_number | int      | Nullable (file-level violations)             |
| message     | string   | Human-readable violation description         |
| remediation | string   | Suggested fix                                |
| state       | enum     | NEW, ACKNOWLEDGED, RESOLVED, OVERRIDDEN      |
| created_at  | datetime | Immutable                                    |
| resolved_at | datetime | Nullable; set on state → RESOLVED/OVERRIDDEN |
| commit_sha  | string   | Git commit that triggered the check          |

**State Machine**:
```
NEW → ACKNOWLEDGED → RESOLVED
NEW → OVERRIDDEN (via Override)
ACKNOWLEDGED → OVERRIDDEN (via Override)
```

**Relationships**: Belongs to Axiom; optionally linked to Override

---

### TraceLink

| Field       | Type     | Constraints                         |
| ----------- | -------- | ----------------------------------- |
| id          | uuid     | Primary key                         |
| source_type | enum     | CODE, TEST, REQUIREMENT, AXIOM      |
| source_ref  | string   | File path + line or document ID     |
| target_type | enum     | CODE, TEST, REQUIREMENT, AXIOM      |
| target_ref  | string   | File path + line or document ID     |
| link_type   | enum     | implements, validates, traces_to    |
| confidence  | float    | 0.0–1.0; parser-extracted vs manual |
| created_at  | datetime | Immutable                           |

**Validation**: source_type ≠ target_type (no self-referential links)
**Relationships**: Forms the traceability matrix (FR-020)

---

### Decision

| Field         | Type     | Constraints                                  |
| ------------- | -------- | -------------------------------------------- |
| id            | uuid     | Primary key                                  |
| actor         | string   | Agent ID or "human-architect"                |
| actor_type    | enum     | AGENT, HUMAN                                 |
| axiom_id      | string   | FK → Axiom.id                                |
| action        | string   | What was decided                             |
| rationale     | string   | Why                                          |
| criticality   | enum     | low, medium, high, critical                  |
| auto_approved | bool     | True if criticality ≤ medium and checks pass |
| created_at    | datetime | Immutable                                    |

**Routing rule**: criticality ∈ {high, critical} → escalate to Human Architect
**Relationships**: Optionally linked to Escalation

---

### Override

| Field                   | Type     | Constraints                                    |
| ----------------------- | -------- | ---------------------------------------------- |
| id                      | uuid     | Primary key                                    |
| axiom_id                | string   | FK → Axiom.id                                  |
| scope_type              | enum     | FILE, DIRECTORY, COMPONENT                     |
| scope_value             | string   | Path or component name                         |
| rationale               | string   | Required, min 20 chars                         |
| created_by              | string   | Human Architect ID (SSO)                       |
| created_at              | datetime | Immutable                                      |
| expires_at              | datetime | Default: created_at + 90 days                  |
| is_permanent            | bool     | Default false; requires elevated justification |
| permanent_justification | string   | Required when is_permanent = true              |
| revoked_at              | datetime | Nullable; set on manual revocation             |

**Lifecycle**:
```
ACTIVE → EXPIRED (auto, on expires_at)
ACTIVE → REVOKED (manual)
```

**Invariants**:
- `is_permanent = true` requires `permanent_justification` non-empty
- System sends notification 7 days before `expires_at`
- Expired overrides auto-revert affected violations to enforcement

---

### Attestation

| Field            | Type         | Constraints                                |
| ---------------- | ------------ | ------------------------------------------ |
| id               | uuid         | Primary key                                |
| agent_id         | string       | Agent identifier (e.g., "gemini-2.5-pro")  |
| task_ref         | string       | Task identifier or commit SHA              |
| axioms_checked   | list[string] | List of Axiom.id values checked            |
| all_satisfied    | bool         | True if no violations found                |
| violations_found | list[uuid]   | FK → Violation.id (empty if all_satisfied) |
| confidence_score | float        | 0.0–1.0; agent self-assessed               |
| escalated        | bool         | True if confidence < threshold → escalated |
| created_at       | datetime     | Immutable                                  |

**Invariant**: `confidence_score < 0.7` → `escalated = true`

---

### ComplianceReport

| Field               | Type            | Constraints                                    |
| ------------------- | --------------- | ---------------------------------------------- |
| schema_version      | string          | Semver, e.g., "1.0.0"                          |
| generated_at        | datetime        | Report generation timestamp                    |
| commit_sha          | string          | Git commit checked                             |
| check_duration_ms   | int             | Total check time in milliseconds               |
| checks_run          | list[object]    | Per-engine results: engine, passed, violations |
| violations          | list[Violation] | All violations found                           |
| traceability_matrix | object          | Code→Tests→Reqs→Axioms mapping                 |
| metrics             | object          | Coverage %, violation counts by axiom/severity |
| attestation         | Attestation     | Nullable; present for agent-initiated checks   |

**Format**: JSON; served by CLI (`generate-report`) and HTTP API (`GET /reports`)

## Configuration Schema (.ade-compliance.yml)

```yaml
version: "1.0"
strictness:
  default: enforce          # audit | warn | enforce
  overrides:                # per-axiom overrides
    Π.3.1: warn             # traceability in warn mode for legacy
coverage:
  threshold: 80             # percentage
  strict_paths:             # paths requiring higher coverage
    - src/core/
escalation:
  github_repo: "org/repo"
  retry_max: 5
  retry_timeout_minutes: 15
performance:
  check_timeout_seconds: 10
override:
  default_expiry_days: 90
  notify_before_expiry_days: 7
```
