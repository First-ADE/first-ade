# Specification: ADE Compliance Framework

This is the official, canonical specification for the ADE Compliance Framework service. All feature development starts from this document and ends with its updates being integrated back here.

---

## 🏛️ Axioms & Governing Postulates

The framework operates as a constitutional enforcement layer under the following constraints:
- **Π.1.1**: Every feature must have an approved specification in the canonical location.
- **Π.2.1**: All implementation code must have matching unit or integration test assertions in the `tests/` directory.
- **Π.3.1**: All code and test files must contain explicit trace comments linking them to axioms and requirements:
  - `# implements: FR-XXX`
  - `# traces_to: Π.X.Y`
- **Π.4.1**: Architectural changes must be documented via Architecture Decision Records (ADRs) using the `pyadr` CLI.
- **Π.5.3**: Agents must self-govern and escalate to a Human Architect after 3 consecutive failures.

---

## Clarifications

- **HTTP API / MCP Gateway**: The common compliance interface (FR-018) is implemented initially as a local HTTP API, evolving into an MCP server with RAG support.
- **Decision Volume**: Expected daily volume is low (hundreds of decisions/violations per day per local developer machine).
- **Human Architect SSO Override**: Critical overrides require a digital signature header (`X-SSO-User`). Overrides are scoped to `FILE`, `DIRECTORY`, or `COMPONENT`. They default to a 90-day expiration, and permanent overrides require elevated validation.
- **Fail-Closed Policy**: If GitHub or communication channels are down, escalations queue locally. If retries exhaust, the framework blocks subsequent agent operations (returning exit code 3) to prevent non-compliant drift.
- **Strictness Levels**: Configurable per-axiom strictness levels: `audit` (log only), `warn` (warn with acknowledgment), and `enforce` (block commit).

---

## User Scenarios & Testing

### US-1 — Compliance Gate at Commit Time (P1)
As a developer (human or agent), I want compliance checks to run automatically on commit so violations are caught before entering the repository.
**Acceptance**:
1. Staging code with no specification → commit blocked, violation report cites Π.1.1
2. Staging code with no test → commit blocked, violation report cites Π.2.1
3. All specs, tests, traceability present → commit proceeds, results logged
4. Blocked commit → report includes axiom violated, affected files, remediation guidance

### US-2 — Specification-First Enforcement (P1)
As an agent, I want the system to verify specs exist before implementation begins (Π.1.1).
**Acceptance**:
1. No requirements doc in spec directory → task rejected with Π.1.1 error
2. Requirements + design docs exist in correct format → task approved
3. Spec exists but wrong format → specific correction feedback returned

### US-3 — Test-First Enforcement (P1)
As an agent, I want verification that tests exist before writing implementation code (Π.2.1).
**Acceptance**:
1. No corresponding test file → operation blocked, test creation required
2. Test files exist but insufficient coverage (below 80% coverage) → violation raised at configured strictness level
3. Adequate tests exist (≥80% coverage) → operation allowed

### US-4 — Traceability Validation (P2)
As a Human Architect, I want all code to have traceability links to requirements and axioms (Π.3.1).
**Acceptance**:
1. Code with traceability markers → passes check
2. Code without markers → commit blocked, missing links reported
3. Full traceability request → system generates code → tests → requirements → axioms matrix

### US-5 — Human Architect Escalation (P2)
As a Human Architect, I want critical decisions and repeated agent failures escalated automatically while reviewing <5% of all decisions.
**Acceptance**:
1. Agent fails 3 consecutive times (Π.5.3) → escalated with full context
2. High/critical decision → routed to Human Architect
3. Low/medium decision passing checks → auto-approved
4. Architect decides escalation → logged with rationale and axiom reference

#### Criticality Taxonomy Rubric
| Criticality Level | Rule / Event Type | Routing / Action |
| ----------------- | ----------------- | ---------------- |
| **Critical**      | MUST violations (e.g., missing specs/tests, pre-commit failures, core line coverage <80%) | Block operation and immediately Alert Human Architect |
| **High**          | Overrides, consecutive agent failures (3+) | Route to Human Architect for review |
| **Medium**        | Configurable warnings (e.g., non-core coverage <80%, performance timeout budget >10s) | Log warning and allow operations with acknowledgment |
| **Low**           | Checks passing, auto-approvals | Auto-approve and log in the audit trail |

### US-6 — Audit Trail and Reporting (P2)
As a Human Architect, I want an immutable audit trail of all decisions with axiom references.
**Acceptance**:
1. Compliance check completes → results logged (timestamp, actor, decision, axiom, rationale)
2. Override recorded → audit includes rule, rationale, timestamp, affected components
3. 30-day trend report → JSON compliance report with violation counts, trends, severity distributions by axiom; generated on-demand via CLI or HTTP API.

### US-7 — CLI for Manual Checks (P3)
As a developer, I want a CLI to run compliance checks manually before committing.
**Acceptance**:
1. `ade-compliance check-all` → human-readable results with exit codes
2. `ade-compliance check-traceability` → traceability-specific findings
3. `ade-compliance generate-report` → JSON output with schema version

### US-8 — Agent Self-Governance and Attestation (P3)
As an AI agent, I want to self-check compliance before execution and provide attestation upon completion.
**Acceptance**:
1. Pre-execution self-check → identifies potential axiom violations
2. Task completion → attestation lists axioms applied, satisfaction status, agent ID, timestamp
3. Agent confidence below threshold → escalates rather than proceeding

---

## Requirements

### Functional Requirements

- **FR-001**: Verify specification exists before implementation (Π.1.1)
- **FR-002**: Verify test files exist before implementation code creation (Π.2.1)
- **FR-003**: Validate traceability links between code, tests, requirements, and axioms (Π.3.1)
- **FR-004**: Validate specification format against required structure (EARS patterns, correctness properties)
- **FR-005**: Detect architectural changes and verify corresponding ADRs exist (Π.4.1)
- **FR-006**: Block non-compliant operations with detailed violation reports and remediation guidance
- **FR-007**: Log all compliance decisions to an immutable, tamper-evident audit trail (Append-only SQLite)
- **FR-008**: Classify decisions by criticality (low/medium/high/critical); route high/critical to Human Architect
- **FR-009**: Escalate to Human Architect on 3 consecutive agent failures (Π.5.3)
- **FR-010**: Pre-commit hook executes compliance checks and blocks non-compliant commits
- **FR-011**: CLI for individual and combined compliance checks
- **FR-012**: Machine-readable compliance reports (JSON with schema version)
- **FR-013**: Support agent pre-execution compliance self-checks
- **FR-014**: Require agent compliance attestations on task completion
- **FR-015**: Validate test determinism (no external state, timing, or order dependencies) through static analysis (banning `time.sleep`), random execution order (`pytest-randomly`), and mocking of external calls.
- **FR-016**: Enforce configurable test coverage thresholds; block commits below threshold
- **FR-017**: Programmatic API for integrating compliance checks into other tools
- **FR-018**: Common compliance interface via local HTTP API / MCP gateway
- **FR-019**: Support Python, TypeScript, JavaScript, and Java for traceability extraction
- **FR-020**: Generate traceability matrix: code → tests → requirements → axioms
- **FR-021**: Human Architect override of violations with mandatory rationale and scope. 90-day expiration, and permanent overrides require elevated validation.
- **FR-022**: Alert when human-review decisions exceed 5% of overall decisions.
- **FR-023**: Block deployments with unresolved violations unless Human Architect overrides
- **FR-025**: Fail-closed on internal failures — block rather than pass non-compliant code
- **FR-026**: Expose metrics (latency percentiles, violation counts, cache hits, queue depth) via Prometheus `/metrics` endpoint.
- **FR-027**: Three configurable strictness levels per axiom: audit, warn, enforce
- **FR-028**: Queue escalation notifications locally on delivery failure; retry with backoff, blocking active CI processes on final failure.
- **FR-030**: Serialize concurrent checks per-file using standard file-system locks on target file paths.

### Key Entities

| Entity | Description |
| :--- | :--- |
| **Axiom** | ADE principle reference (Axiom `Σ.X` or Postulate `Π.X.Y`) |
| **Violation** | Breach record: severity, file, line, axiom ref, timestamp, state |
| **TraceLink** | Connection (implements, validates, traces_to) between components |
| **Decision** | Recorded choice: actor, axiom ref, rationale, criticality, timestamp |
| **Override** | Human Architect exception: scope, rationale, optional expiration |
| **Attestation** | Agent's signed compliance confirmation: axioms applied, status |
| **ComplianceReport** | JSON summary of checks, traceability, violations, and metrics |

---

## Success Criteria

| ID | Criterion |
| :--- | :--- |
| **SC-001** | Zero axiom violations reach production |
| **SC-002** | All checks complete within 10 seconds |
| **SC-003** | 100% agent work includes compliance attestation |
| **SC-004** | Human Architect reviews <5% of decisions |
| **SC-005** | 100% implementation code has traceability links |
| **SC-006** | 100% architectural decisions have ADRs |
| **SC-007** | Core business logic ≥80% test coverage |
| **SC-008** | All decisions logged — no audit trail gaps |
| **SC-009** | 90% of developers report no workflow disruption |
| **SC-010** | Traceability supports Python, TS, JS, Java |
