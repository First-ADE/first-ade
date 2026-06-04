# implements: FR-001
# traces_to: Π.2.1

from unittest.mock import MagicMock, patch

import pytest

from ade_compliance.hooks.pre_commit import main


def test_pre_commit_success():
    """If check-all succeeds, hook exits 0."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 0
        mock_run.assert_called_once()


def test_pre_commit_remediation_success():
    """If check-all fails but remediate succeeds, hook exits 0."""
    with patch("subprocess.run") as mock_run, patch("pathlib.Path.exists", return_value=True):
        mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=0)]

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 0
        assert mock_run.call_count == 2


def test_pre_commit_remediation_failure():
    """If check-all fails and remediate fails, hook exits 1."""
    with patch("subprocess.run") as mock_run, patch("pathlib.Path.exists", return_value=True):
        mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=1)]

        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 1
        assert mock_run.call_count == 2
