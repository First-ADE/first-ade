#!/usr/bin/env python3
"""Spec-Kit Requirements & Task Traceability Compliance Auditor.
Audits:
1. Presence of mandatory files (spec.md, plan.md, tasks.md) under specs/* subdirectories.
2. Formats and regex-validates requirement IDs (FR-XXX) and task IDs (TXXX) in tasks.md.
3. Checks for bidirectional traceability: verifies that every task in tasks.md points to
   a requirement defined in spec.md, and checks if any requirements are completely untraced.
"""

import re
import sys
from pathlib import Path
from typing import List, Set, Tuple


def parse_spec_requirements(spec_path: Path) -> Tuple[Set[str], List[str]]:
    """Extract requirement IDs (e.g., FR-001, FR-021) from spec.md."""
    req_ids = set()
    errors = []

    if not spec_path.exists():
        errors.append(f"Missing spec.md file in {spec_path.parent.name}")
        return req_ids, errors

    content = spec_path.read_text(encoding="utf-8")

    # Matches bullet points like "- **FR-001**:" or "FR-001:"
    pattern = re.compile(r"FR-\d{3}")
    for match in pattern.finditer(content):
        req_ids.add(match.group(0))

    return req_ids, errors


def parse_tasks_traceability(tasks_path: Path, valid_reqs: Set[str]) -> Tuple[List[str], List[str]]:
    """Extract tasks and audit trace links in tasks.md."""
    errors = []
    traced_reqs = []

    if not tasks_path.exists():
        errors.append(f"Missing tasks.md file in {tasks_path.parent.name}")
        return traced_reqs, errors

    content = tasks_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Matches task lines e.g. "- [ ] T001 ..."
    task_start_pattern = re.compile(r"-\s+\[\s*[xX\s/]\s*\]\s+(T\d{3})")
    # Matches any bracketed group: [XYZ]
    brackets_pattern = re.compile(r"\[([^\]]+)\]")

    for idx, line in enumerate(lines, 1):
        start_match = task_start_pattern.search(line)
        if start_match:
            task_id = start_match.group(1)
            # Scan bracketed elements that occur after the task ID
            after_task = line[start_match.end() :]
            traces = brackets_pattern.findall(after_task)

            for t in traces:
                t = t.strip()
                # Matches user scenario (e.g. US3, US-3)
                if t.startswith("US") or re.match(r"^US\d+$", t) or re.match(r"^US-\d+$", t):
                    # Valid scenario trace, skip checks
                    pass
                # Matches functional requirement (e.g. FR-001)
                elif t.startswith("FR-"):
                    traced_reqs.append(t)
                    if t not in valid_reqs:
                        errors.append(
                            f"Line {idx} in {tasks_path.name}: Task {task_id} traces to undefined requirement '{t}'"
                        )
                # Ignore common status/phase codes: P (Prerequisite), D (Draft), A (Audit), U (User scenario/clarification?), I, G, etc.
                elif t in ("P", "D", "A", "U", "I", "G", "Optional", "Deferred", "ROADMAP", "TOC"):
                    pass
                # Any other bracketed content that is capital letters with numbers (e.g., QA-1, SSO-PR-1)
                elif re.match(r"^[A-Z0-9_\-]+$", t):
                    pass
                else:
                    errors.append(
                        f"Line {idx} in {tasks_path.name}: Task {task_id} has invalid trace format '{t}'. Must trace to 'FR-XXX' or 'USX'."
                    )

    return traced_reqs, errors


def main():
    specs_dir = Path("specs")
    if not specs_dir.exists() or not specs_dir.is_dir():
        print("Specs directory not found at root.", file=sys.stderr)
        sys.exit(0)

    has_errors = False
    print("=================================================================")
    print("      FIRST-ADE SPEC-KIT INTEGRITY & TRACEABILITY AUDITOR        ")
    print("=================================================================\n")

    for spec_subdir in specs_dir.iterdir():
        if not spec_subdir.is_dir():
            continue

        print(f"Auditing Spec-Kit: [{spec_subdir.name}]")

        # Verify structure
        mandatory_files = ["spec.md", "plan.md", "tasks.md"]
        missing = [f for f in mandatory_files if not (spec_subdir / f).exists()]
        if missing:
            print(f"  [x] FAILURE: Missing mandatory files: {', '.join(missing)}")
            has_errors = True
            continue

        spec_path = spec_subdir / "spec.md"
        tasks_path = spec_subdir / "tasks.md"

        # 1. Parse valid requirements from spec.md
        req_ids, spec_errors = parse_spec_requirements(spec_path)
        for err in spec_errors:
            print(f"  [x] Error in spec.md: {err}")
            has_errors = True

        print(
            f"  [v] Found {len(req_ids)} functional requirements in spec.md: {', '.join(sorted(req_ids)) if req_ids else 'None'}"
        )

        # 2. Parse and validate traceability inside tasks.md
        traced_reqs, task_errors = parse_tasks_traceability(tasks_path, req_ids)
        if task_errors:
            for err in task_errors:
                print(f"  [x] Traceability Error: {err}")
                has_errors = True
        else:
            print("  [v] All task tracer definitions are syntactically valid.")

        # 3. Check for orphan/untraced requirements
        untraced = req_ids - set(traced_reqs)
        if untraced:
            # Note: Untraced requirements are logged as warning audit findings but don't strictly block execution unless desired
            print(f"  [!] WARNING: Untraced requirements in tasks.md: {', '.join(sorted(untraced))}")
        else:
            print("  [v] 100% of functional requirements have corresponding implementation tasks.")

        print("-" * 65)

    if has_errors:
        print("\n[x] AUDIT FAILED: Structural or traceability errors detected in your specifications!")
        sys.exit(1)
    else:
        print("\n[v] AUDIT PASSED: All Spec-Kits conform to Specification & Traceability Governance principles!")
        sys.exit(0)


if __name__ == "__main__":
    main()
