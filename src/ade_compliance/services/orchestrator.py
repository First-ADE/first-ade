import asyncio
from typing import List

from ..config import Config
from ..engines.spec_engine import SpecEngine
from ..engines.test_engine import TestEngine
from ..models.report import ComplianceReport
from ..services.audit import AuditService


class Orchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.audit = AuditService(config)

        # Initialize engines
        self.engines = []
        if self.config.engines.spec.enabled:
            self.engines.append(SpecEngine(self.config.engines.spec))
        if self.config.engines.test.enabled:
            self.engines.append(TestEngine(self.config.engines.test))

    async def run(self, files: List[str]) -> ComplianceReport:
        all_violations = []

        # Log start
        self.audit.log("RUN_START", {"files_count": len(files)})

        # Run engines concurrently
        tasks = [engine.check(files) for engine in self.engines]
        results = await asyncio.gather(*tasks)

        for violations in results:
            all_violations.extend(violations)

        # Log findings
        self.audit.log("RUN_COMPLETE", {"violations_count": len(all_violations)})

        # Create Report (MVP: assume CWD is repo root)
        report = ComplianceReport(repo_root=".", violations=all_violations)
        return report
