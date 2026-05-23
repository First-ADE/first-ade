"""T062/T063/T066: FastAPI server for ADE Compliance Framework.

Provides HTTP API endpoints for agent self-governance:
- Health check
- Pre-execution compliance checks
- Attestation recording
- Reports and overrides
- Prometheus metrics

Binds to 127.0.0.1 only with single uvicorn worker (T066).
"""

import time
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Query, Header, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from ade_compliance.config import Config, GlobalSettings, load_config
from ade_compliance.observability.metrics import (
    attestation_confidence,
    attestation_total,
    check_duration_seconds,
    compliance_checks_total,
    escalation_total,
    get_metrics_output,
)
from ade_compliance.services.attestation import AttestationService

# --- Request/Response Models ---


class CheckRequest(BaseModel):
    """Request body for /check endpoint."""

    files: List[str] = []


class CheckResponse(BaseModel):
    """Response body for /check endpoint."""

    violations: List[dict] = []
    files_checked: int = 0


class AttestRequest(BaseModel):
    """Request body for /attest endpoint."""

    agent_id: str
    task_id: str
    confidence: float
    axioms_applied: List[str] = []


class AttestResponse(BaseModel):
    """Response body for /attest endpoint."""

    agent_id: str
    task_id: str
    confidence: float
    axioms_applied: List[str]
    status: str
    timestamp: str


class CreateOverrideRequest(BaseModel):
    """Request body for POST /overrides."""

    axiom_id: str
    scope_type: str
    scope_value: str
    rationale: str
    created_by: str
    expires_in_days: int = 90
    is_permanent: bool = False
    permanent_justification: str = ""


# --- App Factory ---


def create_app(
    config_path: Optional[str] = None,
    audit_path: Optional[str] = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config_path: Path to .ade-compliance.yml config file.
        audit_path: Override audit DB path (for testing).

    Returns:
        Configured FastAPI application.
    """
    # Load config
    if config_path and Path(config_path).exists():
        config = load_config(Path(config_path))
    else:
        config = Config()

    # Override audit path if provided (testing)
    if audit_path:
        config = Config(global_settings=GlobalSettings(audit_path=audit_path))

    attestation_service = AttestationService(config)

    app = FastAPI(
        title="ADE Compliance API",
        description="Agent Self-Governance and Attestation API",
        version="0.1.0",
    )

    # --- T062: Health Endpoint ---

    @app.get("/health")
    def health():
        """Liveness probe."""
        return {"status": "healthy"}

    # --- T062: Check Endpoint ---

    @app.post("/check", response_model=CheckResponse)
    async def check(request: CheckRequest):
        """Run pre-execution compliance checks on specified files."""
        start_time = time.monotonic()
        compliance_checks_total.inc()

        violations = await attestation_service.pre_check(request.files)

        duration = time.monotonic() - start_time
        check_duration_seconds.observe(duration)

        violation_dicts = [
            {
                "axiom_id": v.axiom_id,
                "file_path": v.file_path,
                "message": v.message,
                "state": v.state.value if hasattr(v.state, "value") else str(v.state),
            }
            for v in violations
        ]

        return CheckResponse(
            violations=violation_dicts,
            files_checked=len(request.files),
        )

    # --- T062: Attest Endpoint ---

    @app.post("/attest", response_model=AttestResponse)
    def attest(request: AttestRequest):
        """Record a compliance attestation."""
        result = attestation_service.record(
            agent_id=request.agent_id,
            task_id=request.task_id,
            confidence=request.confidence,
            axioms_applied=request.axioms_applied,
        )

        # Update metrics
        attestation_total.labels(status=result.status).inc()
        attestation_confidence.observe(result.confidence)
        if result.status == "escalated":
            escalation_total.inc()

        return AttestResponse(
            agent_id=result.agent_id,
            task_id=result.task_id,
            confidence=result.confidence,
            axioms_applied=result.axioms_applied,
            status=result.status,
            timestamp=result.timestamp.isoformat(),
        )

    # --- T063: Reports Endpoint ---

    @app.get("/reports")
    def reports(limit: int = Query(default=100, ge=1, le=1000)):
        """Get audit trail entries."""
        return attestation_service.audit.get_entries(limit=limit)

    @app.get("/reports/trend")
    def trend_report(days: int = Query(default=30, ge=1, le=365)):
        """Get compliance trends over specified number of days."""
        return attestation_service.audit.get_trend_report(days=days)

    # --- T063: Overrides Endpoint ---

    def get_current_sso_user(x_sso_user: Optional[str] = Header(None, alias="X-SSO-User")) -> str:
        """Validate that the request has a valid SSO user identifier in headers."""
        if not x_sso_user:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized: Missing X-SSO-User SSO authentication header."
            )
        return x_sso_user

    from ade_compliance.services.override import OverrideService
    override_service = OverrideService(config)

    @app.get("/overrides")
    def get_overrides(current_user: str = Depends(get_current_sso_user)):
        """List all currently active compliance overrides (authenticated via SSO)."""
        active = override_service.get_active_overrides()
        return [
            {
                "id": o.id,
                "axiom_id": o.axiom_id,
                "scope_type": o.scope_type,
                "scope_value": o.scope_value,
                "rationale": o.rationale,
                "created_by": o.created_by,
                "created_at": o.created_at.isoformat(),
                "expires_at": o.expires_at.isoformat(),
                "is_permanent": o.is_permanent,
                "permanent_justification": o.permanent_justification,
                "revoked_at": o.revoked_at.isoformat() if o.revoked_at else None,
            }
            for o in active
        ]

    @app.post("/overrides")
    def create_override(request: CreateOverrideRequest, current_user: str = Depends(get_current_sso_user)):
        """Create a new compliance override (Human Architect only, validated via SSO)."""
        if request.created_by != current_user:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: SSO user '{current_user}' does not match created_by '{request.created_by}'"
            )
        try:
            o = override_service.create_override(
                axiom_id=request.axiom_id,
                scope_type=request.scope_type,
                scope_value=request.scope_value,
                rationale=request.rationale,
                created_by=request.created_by,
                expires_in_days=request.expires_in_days,
                is_permanent=request.is_permanent,
                permanent_justification=request.permanent_justification,
            )
            return {
                "id": o.id,
                "axiom_id": o.axiom_id,
                "scope_type": o.scope_type,
                "scope_value": o.scope_value,
                "rationale": o.rationale,
                "created_by": o.created_by,
                "created_at": o.created_at.isoformat(),
                "expires_at": o.expires_at.isoformat(),
                "is_permanent": o.is_permanent,
                "permanent_justification": o.permanent_justification,
            }
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    # --- T064: Metrics Endpoint ---

    @app.get("/metrics")
    def metrics():
        """Prometheus-compatible metrics endpoint (FR-026)."""
        output, content_type = get_metrics_output()
        return Response(content=output, media_type=content_type)

    return app


# Default app instance for uvicorn
app = create_app()
