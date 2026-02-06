---
description: Idle agent self-correction and task discovery
---

# Idle Discovery Loop

## 1. Context Phase
// turbo
1. Review recent conversation summaries (System Interaction).
2. Read `task.md` and `implementation_plan.md` (if present).
3. Read `ROADMAP.md` if available.

## 2. Analysis Phase
1. Check for **Pending Tasks** `[ ]` in `task.md` (Highest Priority).
2. Check for **In-Progress/Blocked** `[/]` or `[-]` items.
   - *Check*: Is the blocker resolved in recent history?
3. If no local tasks:
   - Check `ROADMAP.md` for next milestone.
   - Scan for `TODO` comments in `src/`.

## 3. Prioritization Logic
- **IF** pending task found in `task.md`:
  - **AUTO-START**: Effectively "click" the task.
  - Formulate a `task_boundary` with the task name.
  - **Proceed immediately**.

- **IF** only ambiguous/future tasks found:
  - Draft a proposal.
  - Ask user for confirmation.

## 4. Proposal Phase (If not auto-starting)
1. Formulate a "Next Task" proposal.
2. Detail the exact steps to achieve it.
3. Present to user using `notify_user` tool with `SuggestedResponse`.
