# Feature Specification: Prime-Agent Context Hooks & Alignment

**Feature Branch**: `feat/prime-agent-hooks`  
**Created**: 2026-06-03  
**Status**: Draft  
**Input**: User description: "/speckit-specify - prime and prime-agent-config.yaml are the precommit equivalent of priming an agent's context."

## User Scenarios & Testing

### User Story 1 - Dynamic Pre-Execution Context Priming (Priority: P1)
As a developer or agent, I want my agent context files (`.gemini.md`, `.claude.md`, `copilot-instructions.md`) to be dynamically generated and updated based on my current git worktree state and configured requirements when I start a task, so that the agent has the exact right context without bloating prompt limits.

**Why this priority**: Crucial for ensuring LLM agents have precise, up-to-date constraints, minimizing context windows and avoiding hallucinations.

**Independent Test**: Can be tested by staging a specific file (e.g. `src/ade_compliance/cli.py`), executing `ade-compliance prime`, and verifying that the generated context file explicitly includes rules and constraints tailored to `cli.py` and its related axioms.

**Acceptance Scenarios**:
1. **Given** a `prime-agent-config.yaml` specifying target context documents, **When** I run `ade-compliance prime`, **Then** the system reads active requirements and writes standard markdown files (`.gemini.md`, `.claude.md`) to the root workspace.
2. **Given** staged changes in Git, **When** `ade-compliance prime` is executed, **Then** it parses the staged files and generates a custom `#### Planned Target File Constraints:` block matching those files.

---

### User Story 2 - Post-Execution Alignment & Reconciliation Hook (Priority: P1)
As an architect or maintainer, I want git commit hooks to automatically verify that the changes made by an agent reconcile with the requirements and satisfy constitutional truth assertions, blocking the commit if mismatches exist.

**Why this priority**: Essential to verify that the agent's work is actually aligned with specifications and doesn't pollute repository files.

**Independent Test**: Can be tested by running the post-prime reconciliation checker on staged changes that contain missing `# implements` markers, verifying it blocks and lists the exact missing trace links.

**Acceptance Scenarios**:
1. **Given** staged modifications to source files, **When** the `pre-commit` hook triggers, **Then** it validates that every modified block has corresponding trace links and matches requirements specified in `tasks.md`.
2. **Given** untracked development configuration files (such as `.agents/` or `.gemini/` directories), **When** the validator runs, **Then** it flags them as non-compliant under Principle VIII of the constitution.

---

### User Story 3 - Interactive Prime Hook Installation (Priority: P2)
As a developer, I want to install and configure these context hooks with a single CLI command so that my workspace is fully aligned with minimal manual setup.

**Why this priority**: Boosts ease-of-use and ensures developers and agents set up their local hooks correctly.

**Independent Test**: Run `ade-compliance install-hook --prime` and verify the hook scripts are correctly written and marked executable in `.git/hooks/`.

---

## Edge Cases

- **No `prime-agent-config.yaml` present**: The tool should fallback to sensible defaults (e.g., scanning for `.specify/memory/constitution.md` and `docs/POSTULATES.md` automatically).
- **Staged files deleted mid-run**: The tool must handle missing/deleted staged files gracefully without crashing.
- **Malformed YAML configuration**: Should raise a clear, informative parsing error (avoiding internal stack traces).

---

## Requirements

### Functional Requirements

- **FR-031**: System MUST support defining an agent context priming configuration file (`prime-agent-config.yaml`) at the root of the workspace.
- **FR-032**: System MUST parse the git worktree state (staged files) to dynamically determine the files currently under development.
- **FR-033**: System MUST compile active specifications, postulates, and target file constraints into a unified markdown prompt block.
- **FR-034**: System MUST write the generated prompt block to targets specified in `prime-agent-config.yaml` (e.g. `.gemini.md`, `.claude.md`).
- **FR-035**: System MUST provide a verification/reconciliation subcommand that asserts that modified files adhere to Principle VIII (excluding local configuration folders/files like `.agents/` from git commits).
- **FR-036**: System MUST allow configuring the pre-commit hook to execute both the compliance gate checks and the prime reconciliation checks.
- **FR-037**: The generated context block MUST explicitly define "ADE" (Axiom Driven Engineering) to establish the agent's baseline understanding of its operational constraints and the verification sandbox.

### Key Entities

- **Axiom Driven Engineering (ADE)**: A software engineering methodology and compliance gateway where development flows are strictly derived from and verified against mathematical axioms and constitutional postulates. The ADE framework ensures that all code implementations trace directly back to specifications (intent) and deterministic test assertions (correctness), preventing non-compliant drift.
- **Context Priming**: The process of preparing, injecting, and aligning an agent's context (instruction set, system prompts, active specifications, and code files) at session start.
- **Context Reconciliation**: The verification process checking that changes made by the agent adhere to the spec rules and truth assertions before final commit.

---

## Success Criteria

### Measurable Outcomes

- **SC-011**: Dynamic priming file generation completes in under 500 milliseconds.
- **SC-012**: 100% of generated prompt decorators accurately list constraints for staged files.
- **SC-013**: Attempting to commit files in restricted directories (e.g., local agent configurations in `.agents/`) is blocked by the post-prime reconciliation hook.
- **SC-014**: The generated `.gemini.md` and `.claude.md` files contain the standard ADE definition to ensure agent orientation.
