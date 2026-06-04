# implements: FR-001
# traces_to: Π.5.1

import subprocess
import sys
from pathlib import Path


def main():
    # 1. Run initial compliance checks. If everything is already clean, exit 0 immediately.
    try:
        # Run check-all on the package source files
        res = subprocess.run(["uv", "run", "ade-compliance", "check-all", "src/"], capture_output=True, text=True)
        if res.returncode == 0:
            sys.exit(0)
    except Exception as e:
        print(f"Error running preflight compliance checks: {e}")
        sys.exit(1)

    # 2. Compliance checks failed. Run the self-remediation runner.
    print("Compliance checks failed. Initiating autonomous self-remediation...")

    remediate_path = Path("cli/remediate.py")
    if not remediate_path.exists():
        print("Remediation script cli/remediate.py not found. Blocking commit.")
        sys.exit(1)

    try:
        # Execute cli/remediate.py
        # It handles running checks, fixing violations, staging changes, and checking again.
        res_rem = subprocess.run(["uv", "run", "python", "cli/remediate.py"], capture_output=False)
        if res_rem.returncode == 0:
            print("Self-remediation succeeded. Staged changes and allowed commit.")
            sys.exit(0)
        else:
            print("Self-remediation failed to resolve all violations. Blocking commit.")
            sys.exit(1)
    except Exception as e:
        print(f"Failed to execute remediation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
