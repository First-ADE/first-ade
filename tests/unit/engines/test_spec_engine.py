import pytest
from unittest.mock import Mock, patch
from ade_compliance.engines.spec_engine import SpecEngine
from ade_compliance.config import EngineConfig

@pytest.fixture
def spec_engine():
    config = EngineConfig(enabled=True, strictness="warn")
    return SpecEngine(config)

@pytest.mark.asyncio
async def test_check_no_spec_file(spec_engine):
    # Mock file system to return empty
    with patch("pathlib.Path.glob", return_value=[]):
        violations = await spec_engine.check(["src/main.py"])
        assert len(violations) == 1
        assert violations[0].axiom_id == "Π.1.1"
        assert violations[0].message == "No specification found"

@pytest.mark.asyncio
async def test_check_valid_spec(spec_engine):
    with patch("pathlib.Path.glob", return_value=[Mock()]):
        # Mock glob finding a file
        violations = await spec_engine.check(["src/main.py"])
        assert len(violations) == 0 # Should pass
