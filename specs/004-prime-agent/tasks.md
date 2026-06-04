# Tasks: Prime-Agent Context Hooks & Alignment

**Input**: Design documents from `/specs/004-prime-agent/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

- [ ] **T001** Setup project environment and parse YAML schemas

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] **T002** Implement configuration loader for `prime-agent-config.yaml` in `src/ade_compliance/services/prime.py`

---

## Phase 3: User Story 1 - Dynamic Pre-Execution Context Priming (Priority: P1)

**Goal**: Automatically compile and write agent context files (`.gemini.md`, etc.).

- [ ] **T003** [US1] Implement context priming decorator compiling specification and postulate files.
- [ ] **T004** [US1] Add Git worktree staged changes parsing to target constraints specifically.

---

## Phase 4: User Story 2 - Post-Execution Alignment & Reconciliation Hook (Priority: P1)

**Goal**: Verify trace links and enforce configuration separation rules before commit.

- [ ] **T005** [US2] Implement reconciliation checks asserting no untracked `.agents/` folder commits exist.
- [ ] **T006** [US2] Link reconciliation checks into compliance verification flow.

---

## Phase 5: User Story 3 - Interactive Prime Hook Installation (Priority: P2)

- [ ] **T007** [US3] Add command-line commands to `cli.py` to auto-install hook scripts.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] **T008** Add unit tests for YAML configuration parsing.
- [ ] **T009** Add integration tests for context output generation.
- [ ] **T010** Update documentation and verify all tests pass.
