from ade_compliance.config import Config, load_config


def test_default_config():
    config = Config()
    assert config.global_settings.strictness == "warn"
    assert config.engines.spec.enabled is True


def test_load_from_yaml(tmp_path):
    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("global:\n  strictness: enforce\n")

    config = load_config(config_file)
    assert config.global_settings.strictness == "enforce"
