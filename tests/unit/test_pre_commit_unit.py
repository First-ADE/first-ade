from unittest.mock import MagicMock, patch

import pytest

from ade_compliance.config import Config
from ade_compliance.hooks.pre_commit import get_staged_files, main
from ade_compliance.models.report import ComplianceReport


def test_get_staged_files_success():
    """Verify that get_staged_files correctly parses git diff output."""
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = "src/a.py\nsrc/b.py\n"
        mock_run.return_value = mock_proc

        files = get_staged_files()
        assert files == ["src/a.py", "src/b.py"]
        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=d"], capture_output=True, text=True, check=True
        )


def test_get_staged_files_empty():
    """Verify that get_staged_files returns empty list when no files are staged."""
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.stdout = ""
        mock_run.return_value = mock_proc

        files = get_staged_files()
        assert files == []


def test_get_staged_files_error():
    """Verify that get_staged_files exits 3 when git command fails."""
    import subprocess

    with (
        patch("subprocess.run", side_effect=subprocess.SubprocessError("git error")),
        pytest.raises(SystemExit) as exc_info,
    ):
        get_staged_files()
    assert exc_info.value.code == 3


def test_pre_commit_main_no_files_staged():
    """Verify that pre-commit main exits 0 when no files are staged."""
    with (
        patch("ade_compliance.hooks.pre_commit.get_staged_files", return_value=[]),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 0


def test_pre_commit_main_checks_pass():
    """Verify that pre-commit main exits 0 when all checks pass."""
    mock_report = MagicMock(spec=ComplianceReport)
    mock_report.violations = []
    mock_report.generate_summary.return_value = "All good"

    with (
        patch("ade_compliance.hooks.pre_commit.get_staged_files", return_value=["src/a.py"]),
        patch("ade_compliance.hooks.pre_commit._run_checks", return_value=(mock_report, Config())),
        patch("ade_compliance.hooks.pre_commit.determine_exit_code", return_value=0),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 0


def test_pre_commit_main_checks_fail_enforce():
    """Verify that pre-commit main exits 1 when violations are detected on enforce."""
    mock_report = MagicMock(spec=ComplianceReport)
    mock_report.violations = [MagicMock()]
    mock_report.generate_summary.return_value = "Violations exist"

    with (
        patch("ade_compliance.hooks.pre_commit.get_staged_files", return_value=["src/a.py"]),
        patch("ade_compliance.hooks.pre_commit._run_checks", return_value=(mock_report, Config())),
        patch("ade_compliance.hooks.pre_commit.determine_exit_code", return_value=1),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 1
