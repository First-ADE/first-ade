# implements: FR-027
# traces_to: Π.3.1

from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, EnvSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict

# Constrained strictness type — rejects invalid values at parse time
StrictnessLevel = Literal["enforce", "warn", "audit"]


class ConfigError(Exception):
    """Raised when configuration loading or parsing fails."""


class GlobalSettings(BaseModel):
    strictness: StrictnessLevel = "enforce"
    enabled: bool = True
    audit_path: str = ".ade_compliance/audit.sqlite"
    database_url: Optional[str] = None

    model_config = {"extra": "ignore"}


class EngineConfig(BaseModel):
    enabled: bool = True
    strictness: StrictnessLevel = "enforce"
    min_coverage: Optional[int] = None

    model_config = {"extra": "ignore"}


class Engines(BaseModel):
    spec: EngineConfig = EngineConfig()
    test: EngineConfig = EngineConfig()
    trace: EngineConfig = Field(default_factory=EngineConfig, alias="traceability", validation_alias="traceability")
    adr: EngineConfig = EngineConfig()

    model_config = {"extra": "ignore", "populate_by_name": True}


class EscalationConfig(BaseModel):
    github_repo: str = "First-ADE/first-ade"
    retry_max: int = 5
    retry_timeout_minutes: int = 15

    model_config = {"extra": "ignore"}


class SSOConfig(BaseModel):
    enabled: bool = False
    jwt_secret: Optional[str] = None
    jwt_public_key: Optional[str] = None
    algorithms: List[str] = ["HS256", "RS256"]
    identity_claim: str = "sub"

    model_config = {"extra": "ignore"}


class Config(BaseSettings):
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings, alias="global", validation_alias="global")
    engines: Engines = Field(default_factory=Engines)
    escalation: EscalationConfig = EscalationConfig()
    sso: SSOConfig = SSOConfig()
    axioms: Dict[str, StrictnessLevel] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        env_prefix="ADE_",
        env_nested_delimiter="__",
        extra="ignore",
        populate_by_name=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        def deep_merge(dict1: dict, dict2: dict) -> dict:
            result = dict(dict1)
            for k, v in dict2.items():
                if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                    result[k] = deep_merge(result[k], v)
                else:
                    result[k] = v
            return result

        class CustomEnvSettingsSource(EnvSettingsSource):
            def _load_env_vars(self) -> Mapping[str, str | None]:
                original_vars = super()._load_env_vars()
                mapped_vars = dict(original_vars)
                for k, v in original_vars.items():
                    # 1. Map global -> global_settings (case robustly)
                    if k.lower().startswith("ade_global__"):
                        suffix = k[len("ade_global__") :]
                        prefix = "ade_global_settings__" if k.islower() else "ADE_GLOBAL_SETTINGS__"
                        mapped_vars[f"{prefix}{suffix}"] = v
                    # 2. Map traceability -> trace (case robustly)
                    elif k.lower().startswith("ade_engines__traceability__"):
                        suffix = k[len("ade_engines__traceability__") :]
                        prefix = "ade_engines__trace__" if k.islower() else "ADE_ENGINES__TRACE__"
                        mapped_vars[f"{prefix}{suffix}"] = v
                return mapped_vars

        class MergedSettingsSource(PydanticBaseSettingsSource):
            def __init__(
                self,
                settings_cls: type[BaseSettings],
                env_src: PydanticBaseSettingsSource,
                init_src: PydanticBaseSettingsSource,
            ):
                super().__init__(settings_cls)
                self.env_src = env_src
                self.init_src = init_src

            def __call__(self) -> dict[str, Any]:
                env_data = self.env_src()
                init_data = self.init_src()
                normalized_env = self._normalize_keys(env_data)
                normalized_init = self._normalize_keys(init_data)
                # Prioritize environment variables over initialization/YAML parameters
                return deep_merge(normalized_init, normalized_env)

            def _normalize_keys(self, data: dict[str, Any]) -> dict[str, Any]:
                normalized = {}
                for k, v in data.items():
                    field_name = k
                    for fname, field in self.settings_cls.model_fields.items():
                        if fname == k or field.alias == k:
                            field_name = fname
                            break
                    normalized[field_name] = v
                return normalized

            def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
                return None, field_name, False

        custom_env = CustomEnvSettingsSource(settings_cls)
        return (MergedSettingsSource(settings_cls, custom_env, init_settings),)


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

    # Overlay environment variables starting with ADE_ to ensure proper precedence
    import os

    for key, val in os.environ.items():
        if key.startswith("ADE_"):
            parts = key[4:].lower().split("__")
            mapped_parts = []
            for p in parts:
                if p == "global_settings":
                    p = "global"
                elif p == "trace":
                    p = "traceability"
                mapped_parts.append(p)

            curr = data
            for i, p in enumerate(mapped_parts):
                if i == len(mapped_parts) - 1:
                    curr[p] = val
                else:
                    if p not in curr or not isinstance(curr[p], dict):
                        curr[p] = {}
                    curr = curr[p]

    try:
        return Config(**data)
    except ValidationError as e:
        raise ConfigError(f"Invalid configuration in {path.name}: {e}") from None
