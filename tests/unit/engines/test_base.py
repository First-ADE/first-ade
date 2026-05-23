# implements: FR-002
# traces_to: Π.2.1

from ade_compliance.config import EngineConfig
from ade_compliance.engines.base import BaseEngine


def test_base_engine_should_run():
    class DummyEngine(BaseEngine):
        async def check(self, files):
            return []

    config = EngineConfig(enabled=True)
    engine = DummyEngine(config)
    assert engine.should_run() is True

    config_disabled = EngineConfig(enabled=False)
    engine_disabled = DummyEngine(config_disabled)
    assert engine_disabled.should_run() is False
