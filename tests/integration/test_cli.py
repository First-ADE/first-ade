import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from ade_compliance.cli import main
from ade_compliance.config import Config
from ade_compliance.models.axiom import Violation, ViolationState
from ade_compliance.models.report import ComplianceReport


def test_cli_check_all_no_violations():
    runner = CliRunner()
    with patch("ade_compliance.cli.Orchestrator") as MockOrch:
        instance = MockOrch.return_value

        async def mock_run_empty(*args, **kwargs):
            return ComplianceReport(repo_root=".", violations=[])

        instance.run.side_effect = mock_run_empty

        result = runner.invoke(main, ["check-all", "src/"])
        assert result.exit_code == 0
        assert "Violations: 0" in result.output


def test_cli_check_all_with_violations_warn():
    runner = CliRunner()
    with (
        patch("ade_compliance.cli.Orchestrator") as MockOrch,
        patch("ade_compliance.cli.load_config", return_value=Config()) as mock_load_config,
    ):
        instance = MockOrch.return_value

        async def mock_run(*args, **kwargs):
            return ComplianceReport(
                repo_root=".",
                violations=[
                    Violation(axiom_id="Π.1.1", file_path="foo.py", message="Missing spec", state=ViolationState.NEW)
                ],
            )

        instance.run.side_effect = mock_run

        result = runner.invoke(main, ["check-all", "src/"])
        # strictness defaults to warn, so exit code should be 2
        assert result.exit_code == 2
        assert "Violations: 1" in result.output


def test_cli_check_spec_executes():
    runner = CliRunner()
    with patch("ade_compliance.cli.Orchestrator") as MockOrch:
        instance = MockOrch.return_value

        async def mock_run(*args, **kwargs):
            return ComplianceReport(repo_root=".", violations=[])

        instance.run.side_effect = mock_run

        result = runner.invoke(main, ["check-spec", "src/"])
        assert result.exit_code == 0
        assert "Violations: 0" in result.output


def test_cli_check_test_executes():
    runner = CliRunner()
    with patch("ade_compliance.cli.Orchestrator") as MockOrch:
        instance = MockOrch.return_value

        async def mock_run(*args, **kwargs):
            return ComplianceReport(repo_root=".", violations=[])

        instance.run.side_effect = mock_run

        result = runner.invoke(main, ["check-test", "src/"])
        assert result.exit_code == 0
        assert "Violations: 0" in result.output


def test_cli_check_traceability_executes():
    runner = CliRunner()
    with patch("ade_compliance.cli.Orchestrator") as MockOrch:
        instance = MockOrch.return_value

        async def mock_run(*args, **kwargs):
            return ComplianceReport(
                repo_root=".", violations=[], traceability_matrix={"src/foo.py": {"implements": ["Axiom Π.3.1"]}}
            )

        instance.run.side_effect = mock_run

        result = runner.invoke(main, ["check-traceability", "src/"])
        assert result.exit_code == 0
        assert "Traceability Matrix" in result.output
        assert "Axiom Π.3.1" in result.output


def test_cli_generate_report_outputs_json():
    runner = CliRunner()
    with (
        patch("ade_compliance.cli.Orchestrator") as MockOrch,
        patch("ade_compliance.cli.load_config", return_value=Config()) as mock_load_config,
    ):
        instance = MockOrch.return_value

        async def mock_run(*args, **kwargs):
            return ComplianceReport(
                repo_root=".",
                violations=[
                    Violation(axiom_id="Π.1.1", file_path="foo.py", message="Missing spec", state=ViolationState.NEW)
                ],
            )

        instance.run.side_effect = mock_run

        result = runner.invoke(main, ["generate-report", "src/"])
        assert result.exit_code == 2

        # Verify output is valid JSON
        data = json.loads(result.output)
        assert data["repo_root"] == "."
        assert "version" in data  # checks alias serialization mapping
        assert len(data["violations"]) == 1


def test_cli_override_creation_success():
    runner = CliRunner()
    with patch("ade_compliance.services.override.OverrideService.create_override") as mock_create:
        mock_res = MagicMock()
        mock_res.id = "mock-uuid"
        mock_create.return_value = mock_res

        result = runner.invoke(
            main,
            [
                "override",
                "Π.1.1",
                "--scope-value",
                "src/",
                "--rationale",
                "This rationale is long enough to satisfy constraints and validation.",
                "--created-by",
                "HA-01",
            ],
        )
        assert result.exit_code == 0
        assert "Override created successfully" in result.output
        assert "mock-uuid" in result.output
