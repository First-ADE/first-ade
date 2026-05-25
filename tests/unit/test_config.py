"""Tests for ade_compliance.config — models, cascading logic, and YAML loading."""

import pytest
from pydantic import ValidationError

from ade_compliance.config import (
    Config,
    ConfigError,
    EngineConfig,
    Engines,
    GlobalSettings,
    get_axiom_strictness,
    load_config,
)

# ── Existing tests (preserved) ──────────────────────────────────────────────


def test_default_config():
    config = Config()
    assert config.global_settings.strictness == "enforce"
    assert config.engines.spec.enabled is True


def test_load_from_yaml(tmp_path):
    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("global:\n  strictness: enforce\n")

    config = load_config(config_file)
    assert config.global_settings.strictness == "enforce"


# ── Finding 1.1: Literal strictness validation ──────────────────────────────


def test_invalid_strictness_rejected():
    """Invalid strictness values must be rejected at parse time."""
    with pytest.raises(ValidationError):
        GlobalSettings(strictness="yolo")


def test_invalid_engine_strictness_rejected():
    """EngineConfig also rejects invalid strictness."""
    with pytest.raises(ValidationError):
        EngineConfig(strictness="block")


def test_invalid_axiom_strictness_rejected():
    """Axiom overrides with invalid strictness are rejected."""
    with pytest.raises(ValidationError):
        Config(axioms={"Π.1.1": "nope"})


def test_valid_strictness_values_accepted():
    """All three valid strictness levels are accepted."""
    for level in ("enforce", "warn", "audit"):
        gs = GlobalSettings(strictness=level)
        assert gs.strictness == level


# ── Finding 1.2: Engines populate_by_name ────────────────────────────────────


def test_engines_populate_by_field_name():
    """Engines(trace=...) must work alongside alias='traceability'."""
    custom = EngineConfig(strictness="enforce", enabled=False)
    engines = Engines(trace=custom)
    assert engines.trace.strictness == "enforce"
    assert engines.trace.enabled is False


def test_engines_populate_by_alias():
    """Engines(traceability=...) also works via alias."""
    custom = EngineConfig(strictness="audit")
    engines = Engines(traceability=custom)
    assert engines.trace.strictness == "audit"


# ── Finding 2.1: Cascading strictness logic ──────────────────────────────────


@pytest.fixture
def cascading_config():
    """Config with distinct strictness at every layer for disambiguation."""
    return Config(
        global_settings=GlobalSettings(strictness="warn"),
        engines=Engines(
            spec=EngineConfig(strictness="enforce"),
            test=EngineConfig(strictness="audit"),
            trace=EngineConfig(strictness="enforce"),
            adr=EngineConfig(strictness="audit"),
        ),
        axioms={"Π.1.1": "audit"},
    )


def test_axiom_override_strictness(cascading_config):
    """Layer 1: specific axiom override takes precedence."""
    assert get_axiom_strictness(cascading_config, "Π.1.1") == "audit"


def test_engine_prefix_spec(cascading_config):
    """Layer 2: Π.1.* (non-overridden) resolves to engines.spec."""
    assert get_axiom_strictness(cascading_config, "Π.1.2") == "enforce"


def test_engine_prefix_test(cascading_config):
    """Layer 2: Π.2.* resolves to engines.test."""
    assert get_axiom_strictness(cascading_config, "Π.2.1") == "audit"


def test_engine_prefix_trace(cascading_config):
    """Layer 2: Π.3.* resolves to engines.trace."""
    assert get_axiom_strictness(cascading_config, "Π.3.1") == "enforce"


def test_engine_prefix_trace_parent(cascading_config):
    """Layer 2: Π.3 itself also resolves to engines.trace."""
    assert get_axiom_strictness(cascading_config, "Π.3") == "enforce"


def test_engine_prefix_adr_pi4(cascading_config):
    """Layer 2: Π.4.* resolves to engines.adr."""
    assert get_axiom_strictness(cascading_config, "Π.4.1") == "audit"


def test_engine_prefix_adr_literal(cascading_config):
    """Layer 2: ADR.* also resolves to engines.adr."""
    assert get_axiom_strictness(cascading_config, "ADR.001") == "audit"


def test_unknown_prefix_falls_to_global(cascading_config):
    """Layer 3: unknown prefix falls through to global strictness."""
    assert get_axiom_strictness(cascading_config, "Π.99.1") == "warn"
    assert get_axiom_strictness(cascading_config, "CUSTOM.1") == "warn"


# ── Finding 3.1: YAML parse error handling ───────────────────────────────────


def test_load_missing_file_returns_defaults(tmp_path):
    """Non-existent path returns default Config without error."""
    config = load_config(tmp_path / "nonexistent.yml")
    assert config.global_settings.strictness == "enforce"
    assert config.engines.spec.enabled is True


def test_load_malformed_yaml_raises_config_error(tmp_path):
    """Malformed YAML raises ConfigError, not raw yaml.YAMLError."""
    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("global:\n  strictness: enforce\n  bad_indent")

    with pytest.raises(ConfigError, match="Invalid YAML"):
        load_config(config_file)


def test_load_non_dict_yaml_raises_config_error(tmp_path):
    """YAML that parses to a scalar raises ConfigError."""
    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("just a string")

    with pytest.raises(ConfigError, match="Expected a YAML mapping"):
        load_config(config_file)


def test_load_invalid_fields_raises_config_error(tmp_path):
    """Valid YAML with invalid field types raises ConfigError."""
    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("global:\n  strictness: yolo\n")

    with pytest.raises(ConfigError, match="Invalid configuration"):
        load_config(config_file)


def test_load_empty_yaml_returns_defaults(tmp_path):
    """An empty YAML file returns default Config."""
    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("")

    config = load_config(config_file)
    assert config.global_settings.strictness == "enforce"


def test_load_config_error_does_not_leak_full_path(tmp_path):
    """ConfigError messages must use basename only, not the full path."""
    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("just a string")

    with pytest.raises(ConfigError) as exc_info:
        load_config(config_file)

    error_message = str(exc_info.value)
    # Must contain the basename
    assert ".ade-compliance.yml" in error_message
    # Must NOT contain the full tmp_path
    assert str(tmp_path) not in error_message


# ── Alias integration tests ─────────────────────────────────────────────────


def test_global_alias_from_yaml(tmp_path):
    """YAML key 'global' maps correctly to global_settings."""
    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("global:\n  strictness: audit\n  enabled: false\n")
    config = load_config(config_file)
    assert config.global_settings.strictness == "audit"
    assert config.global_settings.enabled is False


def test_traceability_alias_from_yaml(tmp_path):
    """YAML key 'traceability' maps correctly to engines.trace."""
    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("engines:\n  traceability:\n    strictness: enforce\n    enabled: false\n")
    config = load_config(config_file)
    assert config.engines.trace.strictness == "enforce"
    assert config.engines.trace.enabled is False


# ── Environment override tests ──────────────────────────────────────────────


def test_env_var_override_global(monkeypatch):
    """Environment variables with 'ADE_' prefix override global settings."""
    monkeypatch.setenv("ADE_GLOBAL__STRICTNESS", "audit")
    monkeypatch.setenv("ADE_GLOBAL__ENABLED", "false")
    monkeypatch.setenv("ADE_GLOBAL__AUDIT_PATH", "env_path.sqlite")

    config = Config()
    assert config.global_settings.strictness == "audit"
    assert config.global_settings.enabled is False
    assert config.global_settings.audit_path == "env_path.sqlite"


def test_env_var_override_engine(monkeypatch):
    """Environment variables with 'ADE_' prefix override nested engine config."""
    monkeypatch.setenv("ADE_ENGINES__TEST__MIN_COVERAGE", "95")
    monkeypatch.setenv("ADE_ENGINES__TEST__STRICTNESS", "warn")
    monkeypatch.setenv("ADE_ENGINES__SPEC__ENABLED", "false")

    config = Config()
    assert config.engines.test.min_coverage == 95
    assert config.engines.test.strictness == "warn"
    assert config.engines.spec.enabled is False


def test_env_var_override_with_yaml_fallback(tmp_path, monkeypatch):
    """Environment variables override values loaded from a YAML configuration file."""
    config_file = tmp_path / ".ade-compliance.yml"
    config_file.write_text("global:\n  strictness: enforce\n  enabled: true\nengines:\n  test:\n    min_coverage: 80\n")

    monkeypatch.setenv("ADE_GLOBAL__STRICTNESS", "warn")
    monkeypatch.setenv("ADE_ENGINES__TEST__MIN_COVERAGE", "90")

    config = load_config(config_file)
    assert config.global_settings.strictness == "warn"  # overridden by env
    assert config.global_settings.enabled is True  # fallback to YAML
    assert config.engines.test.min_coverage == 90  # overridden by env
