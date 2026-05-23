# implements: FR-002
# traces_to: Π.2.1

import pytest
from ade_compliance.config import Config
from ade_compliance.services.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    config = Config()
    config.global_settings.audit_path = ":memory:"
    
    orch = Orchestrator(config)
    assert len(orch.engines) > 0


@pytest.mark.asyncio
async def test_orchestrator_run_empty():
    config = Config()
    config.global_settings.audit_path = ":memory:"
    
    orch = Orchestrator(config)
    report = await orch.run([])
    assert len(report.violations) == 0
