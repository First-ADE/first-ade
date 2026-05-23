# Adopt Axiom Driven Engineering

* Status: accepted
* Deciders: First-ADE Founding Team
* Date: 2026-02-06

Technical Story: Foundational methodology setup

## Context and Problem Statement

The First-ADE organization needed a foundational decision-making framework that:

1. Grounds all decisions in verifiable first principles
2. Provides traceability from implementation to requirements
3. Enables effective human-AI collaboration
4. Integrates lessons from BDD, TDD, DDD, and Specification-Driven Development

Without a clear methodology, engineering decisions become ad-hoc, rationale is lost, and technical debt accumulates invisibly.

## Considered Options

1. Traditional Agile - Lacks the formal traceability ADE requires
2. Pure TDD - Covers verification but not specification or rationale
3. DDD alone - Strong domain modeling but no test-first mandate
4. Custom ad-hoc process - Inconsistent and undocumented

## Decision Outcome

Chosen option: We adopt Axiom Driven Engineering (ADE) as the foundational methodology for all First-ADE projects.

ADE consists of:
* 5 Core Axioms (S.1-S.5) - Fundamental truths
* 3 Orders of Postulates (P.X.Y) - Derived practices
* Constitutional Governance - Quality gates and enforcement
* ADR Mandates - Traceability for all decisions
* Spec-Kit Lifecycle - Executable methodology

All projects under First-ADE will:
* Include .specify/ folders for specifications
* Follow Red-Green-Refactor commit patterns
* Maintain ADRs for significant decisions
* Provide AI context files for agent collaboration

### Positive Consequences

* All decisions are traceable to first principles
* New contributors understand why not just what
* AI agents have explicit guidance via constitutions
* Technical debt is visible and justified

### Negative Consequences

* Higher upfront documentation effort
* Learning curve for ADE concepts
* May feel bureaucratic for small changes

## Axiom Traceability

* Root Axiom: S.3 (Traceable Rationale)
* Supporting Axioms: S.1 (Specification Primacy), S.2 (Deterministic Verification), S.5 (AI Symbiosis)
* Governing Postulate: P.3.1 (ADRs required for all architectural changes)
