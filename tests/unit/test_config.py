from ade_compliance.config import load_config, Config, EngineConfig, Engines, GlobalSettings
from pathlib import Path

def test_default_config():
    config = Config()
    assert config.global_settings.strictness == "warn"
    assert config.global_settings.enabled is True
    assert config.engines.spec.enabled is True
    assert config.engines.test.min_coverage is None
