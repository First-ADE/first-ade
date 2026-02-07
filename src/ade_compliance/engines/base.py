from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.axiom import Violation
from ..config import EngineConfig

class BaseEngine(ABC):
    def __init__(self, config: EngineConfig):
        self.config = config
        
    @abstractmethod
    async def check(self, files: List[str]) -> List[Violation]:
        """Run compliance checks against the provided files."""
        pass
        
    def should_run(self) -> bool:
        return self.config.enabled
