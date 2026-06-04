# Implementation Plan: Autonomous Self-Remediation Loop

**Branch**: `feat/local-self-remediation` | **Date**: 2026-06-03 | **Spec**: [spec.md](file:///c:/Users/bfoxt/OneDrive/Desktop/First-ADE/first-ade/specs/003-self-remediation/spec.md)  
**Input**: Feature specification from `/specs/003-self-remediation/spec.md`

## Summary

The goal of this feature is to establish a local-first, zero-external-API self-remediation system that runs in the developer pre-commit hook and GitHub Actions CI. We will implement `cli/remediate.py`, which is triggered automatically when quality gates fail. The script executes simple AST-based edits for trace link missing errors, and loads `qwen2.5-coder-1.5b` (GGUF format) using `llama-cpp-python` locally to repair test files on the CPU when no local Ollama instance is found.

## Technical Context

*   **Language/Version**: Python 3.12  
*   **Primary Dependencies**: `llama-cpp-python` (CPU version), `tree-sitter`, `ast`, `jinja2` (for prompts)  
*   **Storage**: Local files and Git repository config (`.ade-compliance.yml`, `report.json`)  
*   **Testing**: `pytest` and `pytest-asyncio`  
*   **Target Platform**: Linux (CI runner), Windows 11 (Developer machines)  
*   **Project Type**: Single project Python package  
*   **Performance Goals**: AST program fixes in under 1 second; CPU-only LLM inference completes in under 30 seconds.  
*   **Constraints**: Max 3 iterations to prevent resource loop; zero external API requests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

*   **Π.5.1**: Operates entirely within constitutional bounds (zero external leakage of developer code).
*   **Π.5.3**: Enforces a strict 3-iteration max retry limit before failing closed and notifying the user.

## Project Structure

### Documentation (this feature)

```text
specs/003-self-remediation/
├── spec.md              # Requirements specification
├── plan.md              # This design plan
└── tasks.md             # Work breakdown listing GitHub Issues
```

### Source Code (repository root)

```text
cli/
└── remediate.py         # Autonomous remediation runner (AST rules + llama-cpp)

src/ade_compliance/
├── hooks/
│   └── pre_commit.py    # Modified to invoke remediate.py on check failure
└── config.py            # Configuration options for local models

.github/
└── workflows/
    └── self-improvement.yml # Self-remediation CI runner
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Local Model Loading** | Requires compiling C/C++ bindings in CI runner for `llama-cpp-python`. | Rejected cloud APIs due to the strict "no external API calls" requirement to maintain 100% privacy and cost-free operation. |
