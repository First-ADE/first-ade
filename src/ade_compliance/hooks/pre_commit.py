# implements: FR-010
# traces_to: Π.5.1b

import subprocess
import sys
from typing import List

from ade_compliance.cli import _run_checks, determine_exit_code


def get_staged_files() -> List[str]:
    """Retrieve list of currently staged files from git."""
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=d"], capture_output=True, text=True, check=True
        )
        return [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"Pre-commit error querying git: {e}", file=sys.stderr)
        # Fail-closed policy on internal errors
        sys.exit(3)


def main() -> None:
    """Entry point for git pre-commit hook validation."""
    staged = get_staged_files()
    if not staged:
        # No files staged, skip check
        sys.exit(0)

    config_path = ".ade-compliance.yml"
    try:
        report, cfg = _run_checks(staged, config_path)
        print(report.generate_summary())
        exit_code = determine_exit_code(report.violations, cfg)
        sys.exit(exit_code)
    except Exception as e:
        print(f"Pre-commit gate failed with internal error: {e}", file=sys.stderr)
        # Fail-closed policy
        sys.exit(3)


if __name__ == "__main__":
    main()
