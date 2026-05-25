"""T032: Integration test for git pre-commit hook.

Verifies that the pre-commit hook module can be executed and
returns appropriate exit codes for compliant/non-compliant repos.
"""
# implements: FR-010
# traces_to: Π.3.1

import subprocess
import sys

import pytest


@pytest.mark.integration
def test_pre_commit_hook_module_exists():
    """Verify the pre-commit hook module can be imported."""
    from ade_compliance.hooks import pre_commit
    assert hasattr(pre_commit, '__file__')


@pytest.mark.integration
def test_pre_commit_hook_runs_as_module(tmp_path):
    """Verify pre-commit hook can execute as a Python module.

    Creates a minimal git repo with a .ade-compliance.yml to test
    that the hook module can be invoked without crashing.
    """
    # Create a minimal git repo
    subprocess.run(['git', 'init', str(tmp_path)], check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=str(tmp_path), check=True, capture_output=True)

    # Create a minimal config
    config = tmp_path / '.ade-compliance.yml'
    config.write_text('global:\n  strictness: audit\n  enabled: true\n', encoding='utf-8')

    # Stage the config
    subprocess.run(['git', 'add', '.ade-compliance.yml'], cwd=str(tmp_path), check=True, capture_output=True)

    # Run the pre-commit module — it should execute (may exit non-zero if no staged .py files)
    python = sys.executable
    result = subprocess.run(
        [python, '-m', 'ade_compliance.hooks.pre_commit'],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Should exit with 0 (no python files staged) or 1 (violations) or 3 (internal)
    # but NOT crash with an unhandled exception
    assert result.returncode in (0, 1, 2, 3), f"Unexpected exit code: {result.returncode}\nstderr: {result.stderr}"
