import pytest
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path
from ade_compliance.engines.spec_engine import SpecEngine
from ade_compliance.config import EngineConfig
from ade_compliance.models.axiom import ViolationState

@pytest.fixture
def spec_engine():
    config = EngineConfig(enabled=True, strictness="warn")
    return SpecEngine(config)

@pytest.fixture
def disabled_engine():
    config = EngineConfig(enabled=False, strictness="warn")
    return SpecEngine(config)

def test_spec_engine_no_specs(spec_engine):
    """When no spec files exist, a violation should be generated."""
    with patch.object(Path, 'glob', return_value=[]):
        violations = asyncio.run(spec_engine.check(["src/foo.py"]))
    assert len(violations) == 1
    assert violations[0].axiom_id == "\u03a0.1.1"
    assert violations[0].state == ViolationState.NEW

def test_spec_engine_with_specs(spec_engine):
    """When spec files exist, no violations should be generated."""
    with patch.object(Path, 'glob', side_effect=[
        [Path("specs/001/spec.md")],  # First glob finds files
        []  # Second glob
    ]):
        violations = asyncio.run(spec_engine.check(["src/foo.py"]))
    assert len(violations) == 0

def test_spec_engine_disabled(disabled_engine):
    """When engine is disabled, no checks are run."""
    violations = asyncio.run(disabled_engine.check(["src/foo.py"]))
    assert len(violations) == 0

def test_spec_engine_should_run_enabled(spec_engine):
    assert spec_engine.should_run() is True

def test_spec_engine_should_run_disabled(disabled_engine):
    assert disabled_engine.should_run() is False
