# Harden default quality gate strictness to enforce

* Status: accepted
* Deciders: brandon-fox
* Date: 2026-05-23

Technical Story: [Issue #54](https://github.com/First-ADE/first-ade/issues/54)

## Context and Problem Statement

Constitution Principle VII mandates that "Core business logic MUST maintain >=80% line coverage" and that this threshold is a hard Quality Gate blocker. However, the default strictness level for coverage violations was configured as `warn` in the codebase and task descriptions. This creates a compliance loophole where developers and agents are warned about coverage drops but not blocked from pushing or merging non-compliant code. How can we ensure that all quality gates are strictly blocking by default?

## Governing Postulate

* **P.2.1**: All features shall have failing tests before implementation.
* **P.2.1a**: Tests shall be deterministic and isolated.

## Decision Drivers

* **Constitution Principle VII**: Hard blocker coverage requirements.
* **Axiom Acceptance (S.5)**: Strict validation guarantees for agentic collaboration.
* **Git Hygiene**: Prevent non-compliant states from reaching upstream.

## Considered Options

* **Option 1**: Keep legacy default `warn` and rely on developers to configure `enforce`.
* **Option 2**: Hardcode strictness as `enforce` for only the test coverage engine.
* **Option 3**: Harden all default strictness parameters to `enforce` in the YAML configuration and library codebase defaults.

## Decision Outcome

Chosen option: **Option 3**, because it establishes a zero-tolerance compliance gate across all engines (spec-first, test-first, traceability, ADR detection), preventing any regression from entering the main codebase.

### Positive Consequences

* Full compliance with Constitution Principle VII is enforced by default.
* Seamless pre-commit hook blockages for any missing requirements, missing tests, or insufficient coverage.

### Negative Consequences

* Higher friction during local development as any failure will block the quality gates unless an active SSO/cryptographic override is supplied.

## Axiom Traceability

* **S.2**: Quality and correctness can be mathematically formulated.
* **P.2.1**: Test coverage enforcement.
