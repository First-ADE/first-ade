import yaml
from pathlib import Path
from pydantic import BaseModel, Field

from typing import Optional

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
    
    model_config = {"extra": "ignore"}

class Config(BaseModel):
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings, alias="global")
    engines: Engines = Field(default_factory=Engines)
    
    model_config = {"extra": "ignore"}

from pydantic import Field

def load_config(path: Path = Path(".ade-compliance.yml")) -> Config:
    if not path.exists():
        return Config()
        
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
        
    return Config(**data)
