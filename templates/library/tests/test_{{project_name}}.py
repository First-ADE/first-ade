"""Tests for {{project_name}}."""

import pytest


def test_version():
    """Verify package version is accessible."""
    import importlib

    module = importlib.import_module("{{project_name}}")
    assert module.__version__ == "0.1.0"
