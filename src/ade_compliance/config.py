# implements: FR-027
# traces_to: Π.3.1

from pathlib import Path
from typing import Dict, Literal, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError

# Constrained strictness type — rejects invalid values at parse time
StrictnessLevel = Literal["enforce", "warn", "audit"]


class ConfigError(Exception):
    """Raised when configuration loading or parsing fails."""


class GlobalSettings(BaseModel):
    strictness: StrictnessLevel = "enforce"
    enabled: bool = True
    audit_path: str = ".ade_compliance/audit.sqlite"

    model_config = {"extra": "ignore"}


class EngineConfig(BaseModel):
    enabled: bool = True
    strictness: StrictnessLevel = "enforce"
    min_coverage: Optional[int] = None

    model_config = {"extra": "ignore"}


class Engines(BaseModel):
    spec: EngineConfig = EngineConfig()
    test: EngineConfig = EngineConfig()
    trace: EngineConfig = Field(default_factory=EngineConfig, alias="traceability")
    adr: EngineConfig = EngineConfig()

    model_config = {"extra": "ignore", "populate_by_name": True}


class EscalationConfig(BaseModel):
    github_repo: str = "First-ADE/first-ade"
    retry_max: int = 5
    retry_timeout_minutes: int = 15

    model_config = {"extra": "ignore"}


class Config(BaseModel):
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings, alias="global")
    engines: Engines = Field(default_factory=Engines)
    escalation: EscalationConfig = EscalationConfig()
    axioms: Dict[str, StrictnessLevel] = Field(default_factory=dict)

    model_config = {"extra": "ignore", "populate_by_name": True}


def get_axiom_strictness(config: Config, axiom_id: str) -> StrictnessLevel:
    """Cascading strictness lookup:
    1. Check specific axiom strictness (in config.axioms)
    2. Check per-engine strictness based on prefix
    3. Fall back to global strictness
    """
    # 1. Check specific axiom
    if axiom_id in config.axioms:
        return config.axioms[axiom_id]

    # 2. Check engine-specific prefix
    engine_strictness: Optional[StrictnessLevel] = None
    if axiom_id.startswith("Π.1"):
        engine_strictness = config.engines.spec.strictness
    elif axiom_id.startswith("Π.2"):
        engine_strictness = config.engines.test.strictness
    elif axiom_id.startswith("Π.3"):
        engine_strictness = config.engines.trace.strictness
    elif axiom_id.startswith("Π.4") or axiom_id.startswith("ADR"):
        engine_strictness = config.engines.adr.strictness

    if engine_strictness is not None:
        return engine_strictness

    # 3. Global fallback
    return config.global_settings.strictness


def load_config(path: Path = Path(".ade-compliance.yml")) -> Config:
    """Load and validate configuration from a YAML file.

    Returns default Config() if the file does not exist.
    Raises ConfigError for malformed YAML, non-dict structures,
    or invalid field values — using basename only to avoid
    leaking server filesystem paths.
    """
    if not path.exists():
        return Config()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path.name}: {e}") from None

    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise ConfigError(f"Expected a YAML mapping in {path.name}, got {type(data).__name__}")

    try:
        return Config(**data)
    except ValidationError as e:
        raise ConfigError(f"Invalid configuration in {path.name}: {e}") from None
