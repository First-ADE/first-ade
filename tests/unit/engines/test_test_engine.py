import pytest
from unittest.mock import Mock, patch
from ade_compliance.engines.test_engine import TestEngine
from ade_compliance.config import EngineConfig

@pytest.fixture
def test_engine():
    config = EngineConfig(enabled=True, strictness="warn")
    return TestEngine(config)

@pytest.mark.asyncio
async def test_check_no_test_file(test_engine):
    # Mock finding implementation file but NO test file
    # We need to structure the check() logic to infer test path
    # e.g. from src/foo.py -> tests/unit/test_foo.py
    
    with patch("pathlib.Path.exists") as mock_exists:
        # Checking src/main.py
        # Check: tests/unit/test_main.py, tests/test_main.py
        
        # Scenario: implementation exists, test missing
        def side_effect(path):
            p = str(path).replace("\\", "/") # Normalize
            if "src/main.py" in p: return True
            if "test_main.py" in p: return False
            return False
            
        mock_exists.side_effect = side_effect # Not robust for Path objects, but mock call matching better
        
        # Better: Mock Path objects logic directly? 
        # Or mock Engine logic dependencies?
        # TestEngine.find_test_file(impl_path)
        
        # For this check, let's assume we mock builtins or helpers
        # Let's trust the Engine to use Path.exists
        
        # Simpler: TestEngine check calls self.find_test(path). Mock that.
        with patch.object(TestEngine, "find_test_file", return_value=None):
             violations = await test_engine.check(["src/main.py"])
             assert len(violations) == 1
             assert violations[0].axiom_id == "Π.2.1"
             assert "Missing test file" in violations[0].message

@pytest.mark.asyncio
async def test_determinism_check(test_engine):
    from unittest.mock import mock_open
    # Mock existing test file, but content has "time.sleep"
    with patch.object(TestEngine, "find_test_file", return_value="tests/test_main.py"):
         m = mock_open(read_data="import time\ndef test_foo(): time.sleep(1)")
         with patch("builtins.open", m):
             with patch("pathlib.Path.exists", return_value=True):
                 violations = await test_engine.check(["src/main.py"])
                 # Should flag non-determinism
                 assert any("Non-deterministic" in v.message for v in violations)
