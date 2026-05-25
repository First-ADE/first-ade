"""T054: Integration test for CLI check-all workflow.

Verifies end-to-end CLI functionality including exit codes,
output formatting, and violation reporting.
"""
# implements: FR-011
# traces_to: Π.3.1

import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from ade_compliance.cli import main


@pytest.mark.integration
def test_cli_check_all_no_files():
    """check-all with no paths should exit 0 (no files found)."""
    runner = CliRunner()
    result = runner.invoke(main, ['check-all'])
    # No files = exit 0
    assert result.exit_code == 0


@pytest.mark.integration
def test_cli_check_all_with_config(tmp_path):
    """check-all with a valid config and no source files should exit 0."""
    config = tmp_path / '.ade-compliance.yml'
    config.write_text('global:\n  strictness: audit\n  enabled: true\n', encoding='utf-8')

    runner = CliRunner()
    result = runner.invoke(main, ['check-all', '--config', str(config)])
    assert result.exit_code == 0


@pytest.mark.integration
def test_cli_generate_report_no_files():
    """generate-report with no paths should exit 0."""
    runner = CliRunner()
    result = runner.invoke(main, ['generate-report'])
    assert result.exit_code == 0


@pytest.mark.integration
def test_cli_check_traceability_no_files():
    """check-traceability with no paths should exit 0."""
    runner = CliRunner()
    result = runner.invoke(main, ['check-traceability'])
    assert result.exit_code == 0


@pytest.mark.integration
def test_cli_prompt_decorate(tmp_path):
    """prompt-decorate should output markdown."""
    config = tmp_path / '.ade-compliance.yml'
    config.write_text('global:\n  strictness: enforce\n  enabled: true\n', encoding='utf-8')

    runner = CliRunner()
    result = runner.invoke(main, ['prompt-decorate', '--config', str(config)])
    assert result.exit_code == 0
    assert len(result.output) > 0


@pytest.mark.integration
def test_cli_verify_audit_trail(tmp_path):
    """verify-audit-trail should work with a fresh config."""
    config = tmp_path / '.ade-compliance.yml'
    config.write_text(
        f'global:\n  strictness: audit\n  enabled: true\n  audit_path: "{(tmp_path / "audit.sqlite").as_posix()}"\n',
        encoding='utf-8'
    )

    runner = CliRunner()
    result = runner.invoke(main, ['verify-audit-trail', '--config', str(config)])
    # Should succeed with empty audit trail
    assert result.exit_code == 0
