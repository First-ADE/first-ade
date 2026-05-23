import subprocess
import sys


def verify_pr_size(base_ref="main", limit=200):
    try:
        # Fetch base ref first to ensure it's available
        subprocess.run(["git", "fetch", "origin", base_ref], check=True, capture_output=True)
        # Git diff stats: --numstat prints: added deleted path
        result = subprocess.run(
            ["git", "diff", "--numstat", f"origin/{base_ref}...HEAD"], check=True, capture_output=True, text=True
        )
        total_changes = 0
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                added = parts[0]
                deleted = parts[1]
                # If they are numerical (not binary file '-')
                if added.isdigit() and deleted.isdigit():
                    total_changes += int(added) + int(deleted)

        print(f"Total lines modified in this PR: {total_changes}")
        if total_changes > limit:
            print(f"WARNING: PR size ({total_changes} lines) exceeds target guideline of {limit} lines!")
            print("Please split your PR into smaller, focused pull requests if possible.")
            if "--strict" in sys.argv:
                print("FAIL: Enforcing strict PR size limit!")
                sys.exit(1)
        else:
            print(f"✓ PR size is within compliant limits ({total_changes} / {limit} lines).")
    except Exception as e:
        print(f"Error checking PR size: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="main", help="Base branch ref")
    parser.add_argument("--limit", type=int, default=200, help="PR size limit in lines")
    parser.add_argument("--strict", action="store_true", help="Fail build if size limit exceeded")
    args = parser.parse_args()
    verify_pr_size(base_ref=args.base, limit=args.limit)
