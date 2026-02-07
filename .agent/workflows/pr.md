---
description: Push local changes to a GitHub PR using MCP
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Workflow

1. **Identify the repo** — Run `git remote get-url origin` to extract the GitHub `owner/repo`.

2. **Determine changed files** — Run `git status --porcelain` to list uncommitted/staged changes. If no changes exist, inform the user and stop.

3. **Build a branch name** — Derive from the change context:
   - Prefix: `docs/`, `feat/`, `fix/`, `chore/` based on change type
   - Slug: 2–4 word kebab-case summary (e.g., `docs/populate-constitution`)
   - If `$ARGUMENTS` specifies a branch name, use that instead.

4. **Create the branch via MCP** — Use `create_branch` on the GitHub MCP server:
   ```
   owner: <owner>
   repo: <repo>
   branch: <branch-name>
   ```

5. **Push files via MCP** — Use `create_or_update_file` (single file) or `push_files` (multiple files) on the GitHub MCP server. Use a conventional commit message:
   - Format: `<type>: <short description>`
   - Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`

6. **Create the PR via MCP** — Use `create_pull_request`:
   - `title`: Same as the commit message
   - `body`: Include a Summary, Changes list, and any validation notes
   - `head`: `<branch-name>`
   - `base`: `main`

7. **Report** — Output the PR URL and number to the user.

## Notes

- All Git operations for reading state (remote URL, status) use the terminal.
- All write operations (branch, push, PR) use the GitHub MCP server — never `git push`.
- If the user provides specific commit message or PR title, use those exactly.
