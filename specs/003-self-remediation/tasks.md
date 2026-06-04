# Tasks: Autonomous Self-Remediation Loop

**Input**: Design documents from `/specs/003-self-remediation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

This task list tracks the local-first, zero-external-API self-remediation development. Tasks are organized by user story for incremental development.

---

## Phase 1: Setup & Foundational

*   [x] **T001**: Configure build requirements and project dependencies (`llama-cpp-python` and CPU wheel index) in `cli/pyproject.toml`.
*   [x] **T002**: Download and cache the default `qwen2.5-coder-1.5b-instruct.Q4_K_M.gguf` model for local test execution, and add checksum validation in `cli/remediate.py`.

---

## Phase 2: User Story 1 - AST-Based Comment Insertion (Priority: P1)

*   **Goal**: Auto-remedy missing trace link comments (FR-003).
*   **Independent Test**: Remove a trace link in a python file, run the script, and check that the comment is restored.
*   **Tasks**:
    *   [x] **T003** [US1] Implement local AST parsing using standard library `ast` inside `cli/remediate.py`. ([Issue #139](https://github.com/First-ADE/first-ade/issues/139))
    *   [x] **T004** [US1] Create rule-based comment injection logic that finds class/function definition nodes and appends corresponding `# implements` blocks. ([Issue #139](https://github.com/First-ADE/first-ade/issues/139))

---

## Phase 3: User Story 2 - Local CPU LLM Inference (Priority: P1)

*   **Goal**: Auto-rebuild failing tests and code logic using local in-memory GGUF models.
*   **Independent Test**: Intentionally break an assertion in a unit test, verify the local LLM correctly patches the assertion.
*   **Tasks**:
    *   [x] **T005** [US2] Implement the `llama-cpp` loading and execution wrapper in `cli/remediate.py` (loading model weights, compiling prompts, and parsing output code blocks). ([Issue #140](https://github.com/First-ADE/first-ade/issues/140))
    *   [x] **T006** [US2] Write structured system prompts for Qwen2.5-Coder to restrict output code to JSON-formatted diffs. ([Issue #140](https://github.com/First-ADE/first-ade/issues/140))

---

## Phase 4: User Story 3 - Local Ollama Integration (Priority: P2)

*   **Goal**: Fast-path local developer machine checks using a running Ollama daemon.
*   **Tasks**:
    *   [x] **T007** [US3] Implement Ollama port checks (`http://localhost:11434/api/chat`) and fallback logic in `cli/remediate.py`. ([Issue #141](https://github.com/First-ADE/first-ade/issues/141))

---

## Phase 5: User Story 4 - Git Hook and CI Workflow (Priority: P1)

*   **Goal**: Run self-healing gates before blocking commits or merging PRs.
*   **Tasks**:
    *   [x] **T008** [US4] Integrate the `remediate.py` runner into the git pre-commit hook template in `src/ade_compliance/hooks/pre_commit.py`. ([Issue #142](https://github.com/First-ADE/first-ade/issues/142))
    *   [x] **T009** [US4] Implement a hard iteration limit of 3 retries in `remediate.py` to prevent infinite resource utilization. ([Issue #142](https://github.com/First-ADE/first-ade/issues/142))
    *   [x] **T010** [US4] Create `.github/workflows/self-improvement.yml` to trigger the check-remediate-verify loop in GitHub Actions. ([Issue #143](https://github.com/First-ADE/first-ade/issues/143))
