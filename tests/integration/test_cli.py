import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from ade_compliance.cli import main
from ade_compliance.models.report import ComplianceReport
from ade_compliance.models.axiom import Violation, ViolationState

@pytest.fixture
def runner():
    return CliRunner()

def test_cli_run_no_violations(runner):
    """When no violations are found, exit code should be 0."""
    report = ComplianceReport(repo_root=".", violations=[])
    with patch('ade_compliance.cli.Orchestrator') as MockOrch:
        import asyncio
        mock_instance = MockOrch.return_value
        async def fake_run(files):
            return report
        mock_instance.run = fake_run
        result = runner.invoke(main, ['run', '.'])
    # Should complete without error
    assert result.exit_code == 0

def test_cli_run_with_violations(runner):
    """When violations are found, exit code should be 1."""
    violations = [
        Violation(
            axiom_id="\u03a0.1.1",
            file_path="src/foo.py",
            message="No spec found",
            state=ViolationState.NEW
        )
    ]
    report = ComplianceReport(repo_root=".", violations=violations)
    with patch('ade_compliance.cli.Orchestrator') as MockOrch:
        mock_instance = MockOrch.return_value
        async def fake_run(files):
            return report
        mock_instance.run = fake_run
        result = runner.invoke(main, ['run', '.'])
    assert result.exit_code == 1
