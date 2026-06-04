import pytest
from click.testing import CliRunner

from ade_compliance.cli import determine_exit_code, main
from ade_compliance.config import Config
from ade_compliance.models.axiom import Violation


def test_cli_subcommands_registered():
    """Verify that all the required subcommands are registered in Click."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "check-all" in result.output
    assert "check-spec" in result.output
    assert "check-test" in result.output
    assert "check-traceability" in result.output
    assert "check-adr" in result.output
    assert "generate-report" in result.output
    assert "override" in result.output
    assert "verify-audit-trail" in result.output


@pytest.mark.parametrize(
    "violations,global_strictness,expected_code",
    [
        # No violations -> exit code 0
        ([], "warn", 0),
        ([], "enforce", 0),
        # Violation with global_strictness warn -> exit code 2
        ([Violation(axiom_id="X.1", file_path="a.py", message="Err")], "warn", 2),
        # Violation with global_strictness enforce -> exit code 1
        ([Violation(axiom_id="X.1", file_path="a.py", message="Err")], "enforce", 1),
        # Overridden violation -> exit code 0
        ([Violation(axiom_id="X.1", file_path="a.py", message="Err", state="overridden")], "enforce", 0),
        # Resolved violation -> exit code 0
        ([Violation(axiom_id="X.1", file_path="a.py", message="Err", state="resolved")], "enforce", 0),
    ],
)
def test_determine_exit_code_fallback(violations, global_strictness, expected_code):
    """Test determine_exit_code fallback to global strictness settings."""
    cfg = Config()
    cfg.global_settings.strictness = global_strictness
    cfg.engines.spec.strictness = None
    cfg.engines.test.strictness = None
    cfg.engines.trace.strictness = None

    code = determine_exit_code(violations, cfg)
    assert code == expected_code


def test_determine_exit_code_per_engine():
    """Test determine_exit_code with different strictness levels per engine."""
    # Axiom Π.1.1 is SpecEngine (mapped to spec)
    # Axiom Π.2.1 is TestEngine (mapped to test)
    # Axiom Π.3.1 is TraceEngine (mapped to trace)
    v_spec = Violation(axiom_id="Π.1.1", file_path="spec.md", message="Err")
    v_test = Violation(axiom_id="Π.2.1", file_path="foo.py", message="Err")

    cfg = Config()
    cfg.global_settings.strictness = "audit"

    # 1. Spec is enforce -> exit code 1
    cfg.engines.spec.strictness = "enforce"
    cfg.engines.test.strictness = "warn"
    assert determine_exit_code([v_spec], cfg) == 1

    # 2. Spec is audit, Test is warn -> exit code 2
    cfg.engines.spec.strictness = "audit"
    cfg.engines.test.strictness = "warn"
    assert determine_exit_code([v_spec, v_test], cfg) == 2

    # 3. Both are audit -> exit code 0
    cfg.engines.spec.strictness = "audit"
    cfg.engines.test.strictness = "audit"
    assert determine_exit_code([v_spec, v_test], cfg) == 0


def test_override_cli_validation_rationale_too_short():
    """Verify that override command fails when rationale is less than 20 characters."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "override",
            "Π.1.1",
            "--scope-value",
            "src/",
            "--rationale",
            "Too short",
            "--created-by",
            "HA-01",
        ],
    )
    assert result.exit_code != 0
    assert "Rationale must be at least 20 characters" in result.output


def test_override_cli_validation_permanent_requires_justification():
    """Verify that permanent override requires a justification."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "override",
            "Π.1.1",
            "--scope-value",
            "src/",
            "--rationale",
            "This rationale is long enough to pass first check",
            "--created-by",
            "HA-01",
            "--permanent",
        ],
    )
    assert result.exit_code != 0
    assert "Permanent justification is required" in result.output


def test_verify_audit_trail_cli_success():
    """Verify that verify-audit-trail returns success message and exits 0."""
    from unittest.mock import patch

    with patch("ade_compliance.services.audit.AuditService.verify_chain", return_value=(True, [])):
        runner = CliRunner()
        result = runner.invoke(main, ["verify-audit-trail"])
        assert result.exit_code == 0
        assert "fully intact and verified" in result.output


def test_verify_audit_trail_cli_tampered():
    """Verify that verify-audit-trail reports errors and exits 1 on failure."""
    from unittest.mock import patch

    with patch(
        "ade_compliance.services.audit.AuditService.verify_chain", return_value=(False, ["Chain broken at entry 3"])
    ):
        runner = CliRunner()
        result = runner.invoke(main, ["verify-audit-trail"])
        assert result.exit_code == 1
        assert "Tampering or chain corruption detected" in result.output
        assert "Chain broken at entry 3" in result.output


def test_run_checks_directory_expansion(tmp_path):
    """Verify that _run_checks recursively expands directories to supported files."""
    from unittest.mock import MagicMock, patch

    from ade_compliance.cli import _run_checks

    # Create dummy directory structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    py_file = src_dir / "app.py"
    py_file.write_text("print('hello')", encoding="utf-8")
    js_file = src_dir / "index.js"
    js_file.write_text("console.log('hello')", encoding="utf-8")
    txt_file = src_dir / "readme.txt"
    txt_file.write_text("readme", encoding="utf-8")

    sub_dir = src_dir / "components"
    sub_dir.mkdir()
    tsx_file = sub_dir / "Button.tsx"
    tsx_file.write_text("export default Button;", encoding="utf-8")

    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("global:\n  strictness: audit\n", encoding="utf-8")

    with patch("ade_compliance.cli.Orchestrator") as MockOrch:
        instance = MockOrch.return_value
        async def mock_run(files):
            return MagicMock()
        instance.run.side_effect = mock_run

        report, cfg = _run_checks([str(src_dir)], str(config_file))

        # Check that orchestrator.run was called with the expanded files list
        called_args = instance.run.call_args[0][0]
        # Should contain app.py, index.js, Button.tsx but NOT readme.txt
        called_files = [f.replace("\\", "/") for f in called_args]

        assert any(f.endswith("src/app.py") for f in called_files)
        assert any(f.endswith("src/index.js") for f in called_files)
        assert any(f.endswith("src/components/Button.tsx") for f in called_files)
        assert not any(f.endswith("readme.txt") for f in called_files)

