# Adopt Local-First Zero-API Autonomous Self-Remediation Loop

* Status: accepted
* Deciders: Antigravity Coding Assistant, USER
* Date: 2026-06-03

Technical Story: Designing a secure, offline, cost-free compliance and self-remediation engine for autonomous agentic software development.

## Context and Problem Statement

To enable autonomous development and self-improvement loops in First-ADE, we must provide agents with a mechanism to detect and fix compliance violations automatically. However, relying on external, commercial SaaS LLM APIs introduces API key leakage risks, billing liabilities, network dependencies, and workflow blocks. How can we build an autonomous remediation loop that runs entirely offline with zero external API calls in both local environments and free GitHub Actions CI pipelines?

## Governing Postulate

*   **Π.5.1**: AI agents must operate within constitutional constraints and produce verification artifacts.
*   **Π.5.3**: Agents must self-govern and escalate to a Human Architect after 3 consecutive failures.

## Decision Drivers

*   **100% Free Execution**: The framework must execute without requiring paid LLM API keys or cloud billing.
*   **Security & Privacy**: No source code, specifications, or internal tokens should be sent to external commercial API endpoints.
*   **Offline Portability**: The self-building loop must execute consistently on a local developer machine or inside standard GitHub Actions runners.
*   **Self-Healing Compliance**: Violations (e.g. missing trace comments or test skeletons) should be repaired dynamically before blocking development pipelines.

## Considered Options

*   **Option 1**: Use external, paid LLM APIs (e.g., Gemini API, OpenAI) for autonomous remediation, requiring repo secrets and incurring per-token billing.
*   **Option 2**: Adopt a local-first, zero-external-API architecture: running a quantized coding model (e.g., Qwen2.5-Coder-1.5B) in-memory on the local machine or CI runner CPU, paired with static rule-based AST synthesizers.

## Decision Outcome

Chosen option: **Option 2**, because it guarantees 100% offline, private, and cost-free execution. Simple structural violations are auto-remedied programmatically via local Python AST parsing, while complex tasks (like generating unit test assertions) are resolved via quantized CPU inference using `llama-cpp-python` directly inside the GitHub Actions runner.

### Positive Consequences

*   Zero billing or API key maintenance overhead in public repositories.
*   Perfect code privacy—all prompt contexts and generated code patches stay within local environments.
*   Fast execution times (using highly optimized 1.5B quantized GGUF models that load in <2 seconds and execute in <30 seconds on dual-core CPUs).
*   Frictionless self-healing commits that automatically resolve formatting and structural errors before blocking developers.

### Negative Consequences

*   A 1.5B parameter model has less logical reasoning capability than large cloud models, requiring highly structured prompt templates and strict fallback boundaries.
*   Increased local pipeline setup time (compiling llama-cpp bindings inside CI runners).

## Pros and Cons of the Options

### Option 1 (Paid APIs)

*   Good, because large model reasoning is superior for writing complex code tests.
*   Bad, because it requires managing API secrets and introduces variable billing liabilities.
*   Bad, because it violates the offline-first design philosophy.

### Option 2 (Local-First Quantized CPU Runner)

*   Good, because it is 100% free and requires zero API key secrets.
*   Good, because AST-based rule checks handle simple formatting and comment insertions with 100% determinism.
*   Good, because it uses safe, non-executable GGUF model formats.
*   Bad, because local CPU inference takes slightly longer (15-30 seconds) than high-speed cloud APIs.

## Axiom Traceability

*   **Σ.2**: Deterministic Verification.
*   **Σ.5**: AI Collaboration and Self-Governance.
*   **Π.5.3**: Consecutive Failure Escalation.
