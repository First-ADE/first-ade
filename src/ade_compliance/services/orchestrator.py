import asyncio
from pathlib import Path
from typing import List

from ..config import Config
from ..engines.spec_engine import SpecEngine
from ..engines.test_engine import TestEngine
from ..engines.trace_engine import TraceEngine
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
        if self.config.engines.trace.enabled:
            self.trace_engine = TraceEngine(self.config.engines.trace)
            self.engines.append(self.trace_engine)
        else:
            self.trace_engine = None

    async def run(self, files: List[str]) -> ComplianceReport:
        all_violations = []

        # Log start
        self.audit.log("RUN_START", {"files_count": len(files)})

        # Run engines concurrently
        tasks = [engine.check(files) for engine in self.engines]
        results = await asyncio.gather(*tasks)

        for violations in results:
            all_violations.extend(violations)

        # Extract traceability links from all files to compile matrix
        traceability_matrix = {}
        if self.trace_engine:
            all_links = []
            for file_path in files:
                path = Path(file_path)
                if path.exists() and path.suffix.lower() in (".py", ".js", ".ts", ".tsx", ".java"):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                        links = self.trace_engine.extract_links(file_path, content)
                        all_links.extend(links)
                    except Exception:
                        pass
            traceability_matrix = self.trace_engine.generate_matrix(all_links)

        # Log findings
        self.audit.log("RUN_COMPLETE", {"violations_count": len(all_violations)})

        # Create Report
        report = ComplianceReport(
            repo_root=".",
            violations=all_violations,
            traceability_matrix=traceability_matrix,
        )
        return report
