# Feature Specification: Autonomous Self-Remediation Loop

**Feature Branch**: `feat/local-self-remediation`  
**Created**: 2026-06-03  
**Status**: Draft  
**Input**: User description: "Using 100% free setups like github actions, open source services and free limits on LLMs, setup First ADE for autonomous building, development and design, focused on 100% self builds and improvement, requiring no external API calls."

## User Scenarios & Testing

### User Story 1 - Auto-Remedy Structural Violations (Priority: P1)
As a developer or agent, I want structural violation errors (like missing `# traces_to` or `# implements` comments) to be repaired automatically during the pre-commit gate so that my commit is not blocked by formatting rules.

**Why this priority**: Focuses on maximum developer velocity by resolving trivial rules with zero LLM compile time.

**Independent Test**: Can be tested by deleting a `# implements` comment in a source file, executing the gate, and verifying that the comment is restored programmatically without any LLM network calls.

**Acceptance Scenarios**:
1. **Given** a staged source file missing trace comments, **When** the git hook runs, **Then** the AST parser detects the missing links and automatically injects them back.
2. **Given** a new source file, **When** the pre-commit checker runs, **Then** it prompts the user to confirm the linked spec ID and writes the correct comment blocks.

---

### User Story 2 - Local CPU Remediation in GitHub Actions CI (Priority: P1)
As an open-source maintainer, I want CI pull request runs to automatically attempt to fix logical failures (like missing test files or failing assertions) using a free, locally executing LLM in memory so that I don't incur external API costs or leak project keys.

**Why this priority**: Essential to satisfy the 100% free-tier and zero-external-API constraints in public repositories.

**Independent Test**: Can be tested in a CPU-only runner by passing a failing test report, verifying the runner downloads the quantized Qwen2.5-Coder-1.5B GGUF file, executes CPU inference, and fixes the test assertions successfully.

**Acceptance Scenarios**:
1. **Given** a failing test in a GitHub Actions build, **When** the workflow runs, **Then** it downloads the GGUF model from the cache, runs `llama-cpp-python` locally in memory, and writes a working code patch.
2. **Given** a model compilation failure on the runner, **When** the build executes, **Then** it falls back gracefully to a non-LLM check failure block without committing.

---

### User Story 3 - High-Speed Dev-Machine Remediation (Priority: P2)
As a developer, I want the remediation script to use my local GPU-backed Ollama instance if active so that I get near-instantaneous code fixes while editing files.

**Why this priority**: Improves developer experience by utilizing local developer hardware capabilities when available.

**Independent Test**: Can be tested by running the remediation script with Ollama running on `http://localhost:11434` and verifying it completes under 5 seconds.

**Acceptance Scenarios**:
1. **Given** Ollama is active on port 11434, **When** `remediate.py` is invoked, **Then** it makes local HTTP requests to the Ollama endpoint instead of loading a local GGUF model into memory.
2. **Given** Ollama is not running, **When** the script is run, **Then** it falls back to direct `llama-cpp-python` in-memory CPU loading.

---

### User Story 4 - Strict Resource Sandboxing (Priority: P1)
As a project owner, I want the remediation agent to be strictly limited in its run execution time and iteration depth so that a buggy patch doesn't exhaust free GitHub Actions CI runner minutes.

**Why this priority**: Prevents billing liabilities and infinite loop execution.

**Independent Test**: Can be tested by simulating a compliance check that always fails, verifying the agent stops after exactly 3 attempts.

**Acceptance Scenarios**:
1. **Given** a recurring check failure, **When** the agent runs, **Then** it attempts remediation a maximum of 3 times before halting and raising an escalation issue.

---

## Requirements

### Functional Requirements

*   **FR-001**: System MUST execute the remediation script (`remediate.py`) automatically inside the pre-commit hook when active violations are detected.
*   **FR-002**: The remediation script MUST parse `ade-report.json` to identify the files and specific axioms violated.
*   **FR-003**: System MUST resolve simple structural violations (like missing comments) programmatically using standard AST libraries (`ast` / `tree-sitter`) without invoking any LLMs.
*   **FR-004**: System MUST check for local Ollama server availability on `http://localhost:11434` and use its API if active.
*   **FR-005**: If Ollama is not active, the system MUST use `llama-cpp-python` to load a quantized 1.5B GGUF model in-memory and execute inference locally on the CPU.
*   **FR-006**: The local LLM runner MUST verify the SHA-256 hash of the GGUF model before loading it.
*   **FR-007**: The remediation loop MUST enforce a hard maximum limit of 3 repair iterations.
*   **FR-008**: The agent MUST NOT modify the `.github/workflows/` directory to prevent pipeline hijacking.

---

## Success Criteria

### Measurable Outcomes

*   **SC-001**: 100% of simple structural trace failures (Π.3.1) are auto-remedied in under 1 second.
*   **SC-002**: Local CPU LLM inference in GitHub Actions completes in under 45 seconds per remediation block.
*   **SC-003**: Zero external API keys or network requests to third-party LLM providers are made.
*   **SC-004**: Zero infinite agent loops occur; the agent exits after a maximum of 3 failures.
