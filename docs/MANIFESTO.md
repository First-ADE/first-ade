# The ADE Manifesto

**Axiom Driven Engineering: Building Software from First Principles**

---

## The Problem with Modern Development

Software engineering has drifted into a state of **convention-driven development**. We copy patterns without understanding their origins. We adopt frameworks because they're popular, not because they solve our specific problems. We make architectural decisions based on "best practices" that were best for someone else's context.

The result? Accidental complexity. Technical debt born from unjustified decisions. Systems that work, but nobody knows *why* they work.

## The ADE Solution

**Axiom Driven Engineering** proposes a radical return to first principles. Every architectural decision, every code pattern, every tooling choice MUST trace back to a **verifiable axiom** — a fundamental truth we hold as self-evident.

This isn't philosophy for its own sake. It's a **rigorous engineering discipline** that:

1. **Eliminates cargo-culting** — If you can't trace a decision to an axiom, you shouldn't make it
2. **Enables AI collaboration** — Agents can reason about decisions when the rationale is explicit
3. **Reduces technical debt** — Decisions grounded in principles age better than those grounded in trends
4. **Accelerates onboarding** — New team members understand *why*, not just *what*

## Core Inspirations

ADE synthesizes the best of existing methodologies:

| Methodology                    | What We Borrow                        | How ADE Extends It                   |
| ------------------------------ | ------------------------------------- | ------------------------------------ |
| **BDD** (Behavior Driven)      | Human-readable specifications         | Specs derive from postulates         |
| **TDD** (Test Driven)          | Red-Green-Refactor cycle              | Tests verify axiom compliance        |
| **DDD** (Domain Driven)        | Ubiquitous language, bounded contexts | Domain models trace to domain axioms |
| **SDD** (Specification Driven) | Specs before code                     | Specs ARE code contracts             |

## The Axiomatic Hierarchy

```
Axioms (Σ)          — Self-evident truths
    ↓
Postulates (Π)      — Logical derivations
    ↓
Principles          — Governance rules
    ↓
ADRs                — Traced decisions
    ↓
Specifications      — Executable contracts
    ↓
Implementation      — Axiom-aligned code
```

Every line of code should have a traceable path back to an axiom. This is not bureaucracy — it's **engineering rigor**.

## AI-Native by Design

ADE is built for human-AI collaboration:

- **Humans** define axioms and approve postulates
- **Agents** derive implementation from specifications
- **ADRs** provide the shared language both understand
- **Verification** is automated, deterministic, and trustworthy

The architect thinks in axioms. The agent executes in code. The specification is the contract between them.

## The ADE Pledge

We commit to:

0. **Accept and internalize axioms** — No work begins without explicit acceptance
1. **Scenario before Test** — No test is defined until a User Scenario is committed (BDD)
2. **Test before Code** — No code is written until a failing test is written (TDD)
3. **Specify before implement** — All behavior must be traced to executable specifications
4. **Trace every decision** — Every architectural choice links to governing axioms
5. **Verify deterministically** — Tests that prove, not just assert
6. **Document the why** — Rationale over ritual
7. **Embrace AI symbiosis** — Humans architect, agents execute

---

*Building on first principles, one axiom at a time.*

**Version**: 1.0.0 | **Established**: 2026-02-06
