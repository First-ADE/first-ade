# First-ADE GitHub Organization Documentation

This document defines the structure, governance, repository layouts, and contribution gates for the First-ADE open-source organization on GitHub.

---

## 🏛️ 1. GitHub Organization Structure

All repositories under the `First-ADE` organization adhere to a unified permission, labeling, and governance structure.

### Active Repositories
*   **`First-ADE/first-ade` (Core Monorepo)**: The primary open-source workspace containing the CLI engine (`cli/`), the Model Context Protocol server (`mcp/`), and the GitHub Action compiler (`github-action/`).
*   **`First-ADE/first-ade-obsidian-vault` (Memory Submodule)**: The dedicated knowledge repository synchronized with individual workspaces to host ADR logs, design patterns, and constitutional memory.

---

## 🔒 2. Repository Permissions & Access Levels

To protect the integrity of the core proof systems, the organization enforces three tiers of access:

| Role | Access Scope | Git Permissions | Responsibilities |
| :--- | :--- | :--- | :--- |
| **Human Architect (Maintainer)** | Whole Organization | Admin / Write | Approves architectural changes (ADRs), signs compliance overrides, and merges PRs. |
| **Agent / Contributor** | Designated Repository | Read / Write (Branches) | Submits feature implementations and provides compliance attestations. |
| **Public Observer** | Public Repositories | Read | Submits bug reports and proposes feature specifications. |

---

## 🛡️ 3. Branch Protections & Merge Requirements

The primary branch `main` on all repositories is strictly protected under the following rules:

1.  **Mandatory Compliance Run**: Every Pull Request (PR) must trigger and pass the `First-ADE CI Gate` (no active `enforce` level violations).
2.  **No Direct Commits**: All updates must occur on feature branches (`feat/`, `fix/`, `chore/`) or personal forks, and be merged via PR.
3.  **Mandatory Signature Verification**: All commits to `main` must contain verified GPG or SSH signatures.
4.  **Review Requirements**:
    *   Any modification of core axioms (in `docs/AXIOMS.md` or `SPEC.md`) requires explicit approval from at least one **Human Architect**.
    *   Any PR changing files without corresponding test files (`Π.2.1`) is blocked automatically at the PR gateway.

---

## 📋 4. Pull Request Labels & Automation

To categorize pull requests and automate checks, the repository utilizes the following labels:

*   `axiom-change`: Applied when PR modifies axioms, postulates, or the constitution. Requires elevated architect sign-off.
*   `compliance-bypass`: Applied when the PR incorporates a signed override from `ade-compliance.yml`.
*   `agent-submission`: Applied to PRs generated and attested by AI subagents.

---

## 🤝 5. Community Governance Model

First-ADE operates under a **Constitutional Open-Source Governance** model:
1.  **Changes to the Rules**: Postulates ($\Pi$) and Axioms ($\Sigma$) represent the project's "laws." Altering them requires proposing an Architecture Decision Record (ADR) using the `pyadr` tool, which must be voted on and accepted by the Human Architect board.
2.  **Self-Governance**: Contributors are encouraged to run local self-checks (`ade-compliance check-all`) before submitting PRs, reducing CI overhead and maintaining clean build histories.
