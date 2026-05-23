from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, Field


class GlobalSettings(BaseModel):
    strictness: str = "warn"
    enabled: bool = True
    audit_path: str = ".ade_compliance/audit.sqlite"

    model_config = {"extra": "ignore"}


class EngineConfig(BaseModel):
    enabled: bool = True
    strictness: str = "warn"
    min_coverage: Optional[int] = None

    model_config = {"extra": "ignore"}


class Engines(BaseModel):
    spec: EngineConfig = EngineConfig()
    test: EngineConfig = EngineConfig()
    trace: EngineConfig = Field(default_factory=EngineConfig, alias="traceability")
    adr: EngineConfig = EngineConfig()

    model_config = {"extra": "ignore"}


class EscalationConfig(BaseModel):
    github_repo: str = "First-ADE/first-ade"
    retry_max: int = 5
    retry_timeout_minutes: int = 15

    model_config = {"extra": "ignore"}


class Config(BaseModel):
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings, alias="global")
    engines: Engines = Field(default_factory=Engines)
    escalation: EscalationConfig = EscalationConfig()
    axioms: Dict[str, str] = Field(default_factory=dict)

    model_config = {"extra": "ignore", "populate_by_name": True}


def get_axiom_strictness(config: Config, axiom_id: str) -> str:
    """Cascading strictness lookup:
    1. Check specific axiom strictness (in config.axioms)
    2. Check per-engine strictness based on prefix
    3. Fall back to global strictness
    """
    # 1. Check specific axiom
    if axiom_id in config.axioms:
        return config.axioms[axiom_id]

    # 2. Check engine-specific prefix
    engine_strictness = None
    if axiom_id.startswith("Π.1"):
        engine_strictness = config.engines.spec.strictness
    elif axiom_id.startswith("Π.2"):
        engine_strictness = config.engines.test.strictness
    elif axiom_id.startswith("Π.3") or axiom_id.startswith("Π.3.1"):
        engine_strictness = config.engines.trace.strictness
    elif axiom_id.startswith("Π.4") or axiom_id.startswith("ADR"):
        engine_strictness = config.engines.adr.strictness

    if engine_strictness is not None:
        return engine_strictness

    # 3. Global fallback
    return config.global_settings.strictness or "warn"


def load_config(path: Path = Path(".ade-compliance.yml")) -> Config:
    if not path.exists():
        return Config()

    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    return Config(**data)
