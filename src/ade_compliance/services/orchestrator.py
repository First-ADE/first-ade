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

        # Apply active overrides to violations
        from ..services.override import OverrideService
        from ..models.axiom import ViolationState
        from datetime import datetime
        
        override_service = OverrideService(self.config)
        for v in all_violations:
            if override_service.is_override_active(v.axiom_id, v.file_path):
                v.state = ViolationState.OVERRIDDEN
                v.resolved_at = datetime.utcnow()

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
        for v in all_violations:
            self.audit.log(
                "VIOLATION_DETECTED",
                {
                    "axiom_id": v.axiom_id,
                    "severity": v.severity.value if hasattr(v.severity, "value") else str(v.severity),
                    "file_path": v.file_path,
                },
            )
        self.audit.log("RUN_COMPLETE", {"violations_count": len(all_violations)})

        # Check consecutive failures (Π.5.3)
        if len(all_violations) > 0:
            from ..services.escalation import EscalationService
            escalation_service = EscalationService(self.config)
            try:
                if escalation_service.check_consecutive_failures():
                    titles = [f"- {v.file_path}: {v.message}" for v in all_violations]
                    violations_summary = "\n".join(titles)
                    body = (
                        "Agent has failed compliance checks 3 consecutive times.\n\n"
                        "### Current Run Violations:\n"
                        f"{violations_summary}\n\n"
                        "Please review and remediate."
                    )
                    await escalation_service.escalate(
                        "[ADE Escalation] 3 Consecutive Agent Failures: Π.5.3",
                        body
                    )
            except Exception:
                pass

        # Create Report
        report = ComplianceReport(
            repo_root=".",
            violations=all_violations,
            traceability_matrix=traceability_matrix,
        )
        return report
