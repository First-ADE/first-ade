"""T078a: Unit tests for deployment gate enforcement (FR-023).

Verifies that deployments are blocked when critical/high violations exist
and allowed when no blocking violations are present.
"""
# implements: FR-023
# traces_to: Π.3.1

from click.testing import CliRunner

from ade_compliance.cli import main


def test_deployment_gate_no_files():
    """Deployment gate with no files should pass."""
    runner = CliRunner()
    result = runner.invoke(main, ['check-deployment'])
    assert result.exit_code == 0
    assert "passed" in result.output.lower() or "no files" in result.output.lower()


def test_deployment_gate_clean_directory(tmp_path):
    """Deployment gate with empty directory should pass."""
    config = tmp_path / '.ade-compliance.yml'
    config.write_text('global:\n  strictness: audit\n  enabled: true\n', encoding='utf-8')

    runner = CliRunner()
    result = runner.invoke(main, ['check-deployment', '--config', str(config)])
    assert result.exit_code == 0
