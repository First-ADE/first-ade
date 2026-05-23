from unittest.mock import MagicMock, patch

from ade_compliance.config import EngineConfig
from ade_compliance.engines.adr_engine import ADREngine
from ade_compliance.models.axiom import ViolationState


def test_adr_engine_disabled():
    """Verify that the engine does nothing and returns empty list when disabled."""
    config = EngineConfig(enabled=False)
    engine = ADREngine(config)

    assert not engine.should_run()
    # Execute check synchronously in testing since we are in async pytest
    # and engines use async check(...) methods
    # We will await it using a simple event loop run
    import asyncio

    violations = asyncio.run(engine.check(["pyproject.toml"]))
    assert violations == []


def test_adr_engine_no_architectural_changes():
    """Verify that standard changes (e.g. non-architectural source code) do not trigger violations."""
    config = EngineConfig(enabled=True)
    engine = ADREngine(config)

    import asyncio

    violations = asyncio.run(engine.check(["src/ade_compliance/services/audit.py", "tests/unit/test_config.py"]))
    assert violations == []


def test_adr_engine_architectural_change_without_adr():
    """Verify that changing an architectural file without a corresponding ADR raises a Π.3.1 violation."""
    config = EngineConfig(enabled=True)
    engine = ADREngine(config)

    import asyncio

    # pyproject.toml is an architectural file
    violations = asyncio.run(engine.check(["pyproject.toml", "src/ade_compliance/cli.py"]))
    assert len(violations) == 1
    assert violations[0].axiom_id == "Π.3.1"
    assert violations[0].state == ViolationState.NEW
    assert "no ADR created or modified" in violations[0].message


@patch("subprocess.run")
def test_adr_engine_architectural_change_with_adr_success(mock_run):
    """Verify that changing an architectural file along with an ADR passes successfully if pyadr passes."""
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_run.return_value = mock_res

    config = EngineConfig(enabled=True)
    engine = ADREngine(config)

    import asyncio

    violations = asyncio.run(engine.check(["pyproject.toml", "docs/decisions/0002-test.md"]))
    assert violations == []
    mock_run.assert_called_once_with(["pyadr", "check-adr-repo"], capture_output=True, text=True)


@patch("subprocess.run")
def test_adr_engine_architectural_change_with_adr_failure(mock_run):
    """Verify that if pyadr validation fails, a Π.3.2 violation is raised."""
    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stderr = "Validation error: invalid status"
    mock_run.return_value = mock_res

    config = EngineConfig(enabled=True)
    engine = ADREngine(config)

    import asyncio

    violations = asyncio.run(engine.check(["pyproject.toml", "docs/decisions/0002-test.md"]))
    assert len(violations) == 1
    assert violations[0].axiom_id == "Π.3.2"
    assert "pyadr check-adr-repo failed" in violations[0].message
    assert "Validation error" in violations[0].message


def test_orchestrator_loads_adr_engine():
    """Verify that the Orchestrator initializes ADREngine when configured."""
    from ade_compliance.config import Config
    from ade_compliance.services.orchestrator import Orchestrator

    cfg = Config()
    cfg.engines.adr.enabled = True

    orch = Orchestrator(cfg)
    loaded_types = [type(e).__name__ for e in orch.engines]
    assert "ADREngine" in loaded_types
