import pytest
import asyncio
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from ade_compliance.engines.test_engine import TestEngine
from ade_compliance.config import EngineConfig
from ade_compliance.models.axiom import ViolationState

@pytest.fixture
def test_engine():
    config = EngineConfig(enabled=True, strictness="warn")
    return TestEngine(config)

@pytest.fixture
def disabled_engine():
    config = EngineConfig(enabled=False, strictness="warn")
    return TestEngine(config)

# === Missing Test File Tests ===

def test_test_engine_missing_test(test_engine):
    """When no test file exists for an impl file, a violation should be generated."""
    with patch.object(test_engine, 'find_test_file', return_value=None):
        violations = asyncio.run(test_engine.check(["src/foo.py"]))
    assert len(violations) == 1
    assert violations[0].axiom_id == "\u03a0.2.1"
    assert violations[0].state == ViolationState.NEW

def test_test_engine_with_test(test_engine):
    """When test file exists and is clean, no violations should be generated."""
    with patch.object(test_engine, 'find_test_file', return_value="tests/unit/test_foo.py"):
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="def test_foo():\n    assert True\n")):
                violations = asyncio.run(test_engine.check(["src/foo.py"]))
    assert len(violations) == 0

def test_test_engine_non_deterministic_sleep(test_engine):
    """When test file contains time.sleep, a determinism violation should be generated."""
    with patch.object(test_engine, 'find_test_file', return_value="tests/unit/test_foo.py"):
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="import time\ntime.sleep(1)\n")):
                violations = asyncio.run(test_engine.check(["src/foo.py"]))
    assert len(violations) == 1
    assert violations[0].axiom_id == "\u03a0.3.1"

def test_test_engine_non_deterministic_network(test_engine):
    """When test file contains requests.get, a determinism violation should be generated."""
    with patch.object(test_engine, 'find_test_file', return_value="tests/unit/test_foo.py"):
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="import requests\nrequests.get('http://example.com')\n")):
                violations = asyncio.run(test_engine.check(["src/foo.py"]))
    assert len(violations) == 1
    assert violations[0].axiom_id == "\u03a0.3.1"

def test_test_engine_disabled(disabled_engine):
    """When engine is disabled, no checks are run."""
    violations = asyncio.run(disabled_engine.check(["src/foo.py"]))
    assert len(violations) == 0

# === Non-src files are skipped ===

def test_test_engine_skips_non_src(test_engine):
    """Files outside of src/ should be skipped."""
    violations = asyncio.run(test_engine.check(["docs/README.md"]))
    assert len(violations) == 0

def test_test_engine_skips_non_python(test_engine):
    """Non-Python files should be skipped."""
    violations = asyncio.run(test_engine.check(["src/foo.js"]))
    assert len(violations) == 0
