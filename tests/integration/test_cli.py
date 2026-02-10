from unittest.mock import patch

from click.testing import CliRunner

from ade_compliance.cli import main
from ade_compliance.models.axiom import Violation, ViolationState
from ade_compliance.models.report import ComplianceReport


def test_cli_run_no_violations():
    runner = CliRunner()
    # Mock orchestrator run to return empty report
    with patch("ade_compliance.cli.Orchestrator") as MockOrch:
        instance = MockOrch.return_value

        async def mock_run_empty(*args, **kwargs):
            return ComplianceReport(repo_root=".", violations=[])

        instance.run.side_effect = mock_run_empty

        result = runner.invoke(main, ["run", "src/"])
        assert result.exit_code == 0
        assert "Violations: 0" in result.output


def test_cli_run_with_violations():
    runner = CliRunner()
    with patch("ade_compliance.cli.Orchestrator") as MockOrch:
        instance = MockOrch.return_value
        # Use AsyncMock if needed, but Click calls asyncio.run(coro)
        # So we need instance.run to return a future or be async?
        # Since we patch the class, instance.run is a Mock.
        # asyncio.run(mock()) fails if not awaitable.

        # Correctly mock async method
        async def mock_run(*args, **kwargs):
            return ComplianceReport(
                repo_root=".",
                violations=[Violation(axiom_id="X.1", file_path="foo.py", message="Fail", state=ViolationState.NEW)],
            )

        instance.run.side_effect = mock_run

        result = runner.invoke(main, ["run", "src/"])
        assert result.exit_code == 1
        assert "Violations: 1" in result.output
