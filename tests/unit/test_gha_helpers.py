import os
import sys
from unittest.mock import MagicMock, patch

# Since the scripts are under .github/scripts/, we should add it to pythonpath if needed, or import them directly.
# We dynamically add the scripts path to sys.path so we can import them easily.

SCRIPTS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".github", "scripts"))
if SCRIPTS_PATH not in sys.path:
    sys.path.insert(0, SCRIPTS_PATH)

import check_docs_links  # noqa: E402
import verify_commits  # noqa: E402
import verify_pr_size  # noqa: E402


def test_conventional_commits_regex():
    # Valid commit messages
    valid_commits = [
        "feat: add PR size checker",
        "fix(auth): resolve secret leakage detection in runner",
        "docs: update architecture axioms",
        "style(frontend): format portal component code",
        "refactor: decompose lint tasks into custom scripts",
        "test(gha): add unit tests for verification helpers",
        "chore: clean temporary execution files",
        "perf(core): accelerate compliance metadata checks",
        "ci(config): deploy custom github actions workflow gates",
        "build(deps): bump pip lockfile package version",
        "revert: rollback failed diagnostic deployment",
        "feat(gate)!: break compatibility on schema validation",
    ]
    for commit in valid_commits:
        assert verify_commits.CONVENTIONAL_REGEX.match(commit) is not None, f"Should be valid: {commit}"

    # Invalid commit messages
    invalid_commits = [
        "Feat: capitalized type",
        "add pr size checker (no type)",
        "feat(auth) no colon",
        "fix:no-space-after-colon",
        "randomcommit: invalid conventional type",
        "feat(): empty scope not allowed",
    ]
    for commit in invalid_commits:
        assert verify_commits.CONVENTIONAL_REGEX.match(commit) is None, f"Should be invalid: {commit}"


@patch("subprocess.run")
def test_verify_pr_size_compliant(mock_run):
    # Mock git diff returning under 200 lines
    mock_stdout = "150\t20\tsrc/main.py\n10\t5\ttests/test_main.py\n"
    mock_result = MagicMock()
    mock_result.stdout = mock_stdout
    mock_run.return_value = mock_result

    # Should run and output successfully without sys.exit
    with patch("sys.exit") as mock_exit:
        verify_pr_size.verify_pr_size(base_ref="main", limit=200)
        mock_exit.assert_not_called()


@patch("subprocess.run")
def test_verify_pr_size_violating_strict(mock_run):
    # Mock git diff returning over 200 lines
    mock_stdout = "250\t20\tsrc/main.py\n10\t5\ttests/test_main.py\n"
    mock_result = MagicMock()
    mock_result.stdout = mock_stdout
    mock_run.return_value = mock_result

    # Under strict mode, sys.exit(1) must be called
    with patch("sys.argv", ["verify_pr_size.py", "--strict"]):
        with patch("sys.exit") as mock_exit:
            verify_pr_size.verify_pr_size(base_ref="main", limit=200)
            mock_exit.assert_called_once_with(1)


def test_check_docs_links(tmp_path):
    # Setup mock markdown files with valid and broken relative local links
    doc_dir = tmp_path / "docs"
    doc_dir.mkdir()

    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()

    # Create target files
    target_file = doc_dir / "target.md"
    target_file.write_text("Some target content.")

    # Create main document with links
    main_doc = doc_dir / "main.md"
    main_doc.write_text("""
# Main Spec
- [Valid Relative Link](target.md)
- [Valid Absolute Link](/specs/spec.md)
- [Broken Link](missing.md)
- [Web Link](https://github.com/First-ADE/first-ade)
- [Anchor Link](#some-section)
""")

    # Mock finding repo root to return our tmp_path
    with patch("check_docs_links.find_repo_root", return_value=str(tmp_path)):
        # Write specs/spec.md to make /specs/spec.md valid
        spec_file = spec_dir / "spec.md"
        spec_file.write_text("Spec content")

        errors = check_docs_links.check_file_links(str(main_doc))

        # We expect exactly 1 error (broken link missing.md)
        assert len(errors) == 1
        target, resolved = errors[0]
        assert target == "missing.md"
        assert resolved == os.path.normpath(os.path.join(str(doc_dir), "missing.md"))
