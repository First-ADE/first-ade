import re
import subprocess
import sys

CONVENTIONAL_REGEX = re.compile(
    r"^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([a-z0-9_-]+\))?!?: .+$"
)


def verify_commits(base_ref="main"):
    if base_ref.startswith("refs/heads/"):
        base_ref = base_ref[len("refs/heads/"):]
    try:
        subprocess.run(["git", "fetch", "origin", base_ref], check=True, capture_output=True)
        result = subprocess.run(
            ["git", "log", f"origin/{base_ref}..HEAD", "--no-merges", "--format=%s"],
            check=True,
            capture_output=True,
            text=True,
        )
        commits = [c.strip() for c in result.stdout.split("\n") if c.strip()]
        if not commits:
            print("No commits found in PR branch range.")
            return

        failed = False
        print(f"Verifying {len(commits)} commits against Conventional Commit format:")
        for commit in commits:
            if not CONVENTIONAL_REGEX.match(commit):
                print(f'✗ INVALID: "{commit}"')
                failed = True
            else:
                print(f'✓ VALID:   "{commit}"')

        if failed:
            print("\nError: One or more commit messages do not follow Conventional Commits standard.")
            print("Format: type(scope): description  (e.g., feat(auth): add login endpoint)")
            print("Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert")
            sys.exit(1)
        else:
            print("\nAll commit messages are compliant!")
    except Exception as e:
        print(f"Error checking commits: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="main", help="Base branch ref")
    args = parser.parse_args()
    verify_commits(base_ref=args.base)
