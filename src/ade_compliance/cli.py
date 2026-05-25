# implements: FR-008
# traces_to: Π.3.1

"""CLI Command-Line Entry Point for ADE Compliance Auditor."""

import sys
from pathlib import Path
from typing import List

import click

from .config import Config, load_config
from .models.report import ComplianceReport


def determine_exit_code(violations: List, config: Config) -> int:
    """Determine the exit code based on the strictness of active violations.

    - "enforce" violation = exit 1
    - "warn" violation = exit 2
    - "audit" violation / no active violations = exit 0
    """
    from .config import get_axiom_strictness

    active_violations = [
        v for v in violations if hasattr(v, "state") and v.state.value == "NEW"
    ]

    has_enforce = False
    has_warn = False

    for v in active_violations:
        axiom_id = v.axiom_id or ""
        strictness = get_axiom_strictness(config, axiom_id, v.file_path)

        match strictness:
            case "enforce":
                has_enforce = True
            case "warn":
                has_warn = True

    match (has_enforce, has_warn):
        case (True, _):
            return 1
        case (False, True):
            return 2
        case _:
            return 0


def _run_checks(
    files: List[str],
    config_path: str,
    run_spec: bool = True,
    run_test: bool = True,
    run_trace: bool = True,
    run_adr: bool = True,
) -> tuple[ComplianceReport, Config]:
    """Execute validation checks on specified files concurrently.

    Returns the ComplianceReport and loaded Config.
    """
    import asyncio

    from .services.orchestrator import Orchestrator

    # Load Config
    cfg = load_config(Path(config_path))

    # Check if agent is blocked (FR-028 / U3)
    from ade_compliance.services.escalation import EscalationService

    try:
        escalation_service = EscalationService(cfg)
        if escalation_service.is_agent_blocked():
            click.echo(
                "Error: Agent is blocked due to undelivered escalations in the local queue (fail-closed).", err=True
            )
            sys.exit(3)
    except Exception as e:
        click.echo(f"Error checking agent status: {e}", err=True)
        sys.exit(3)

    # Configure active engines
    cfg.engines.spec.enabled = cfg.engines.spec.enabled and run_spec
    cfg.engines.test.enabled = cfg.engines.test.enabled and run_test
    cfg.engines.trace.enabled = cfg.engines.trace.enabled and run_trace
    if hasattr(cfg.engines, "adr"):
        cfg.engines.adr.enabled = cfg.engines.adr.enabled and run_adr

    # Setup orchestrator & run check
    orch = Orchestrator(cfg)
    report = asyncio.run(orch.run(files))
    return report, cfg


@click.group()
def main():
    """First-ADE compliance CLI utility."""
    pass


@main.command(name="check-all")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def check_all(paths: List[str], config: str):
    """Execute all active compliance verification engines."""
    report, cfg = _run_checks(paths, config, run_spec=True, run_test=True, run_trace=True, run_adr=True)
    click.echo(report.generate_summary())
    exit_code = determine_exit_code(report.violations, cfg)
    sys.exit(exit_code)


@main.command(name="generate-report")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
@click.option("--output", "-o", default="ade-report.json", help="Report output destination")
def generate_report(paths: List[str], config: str, output: str):
    """Generate detailed JSON compliance report."""
    report, cfg = _run_checks(paths, config, run_spec=True, run_test=True, run_trace=True, run_adr=True)
    json_data = report.model_dump_json(by_alias=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(json_data)
    click.echo(f"Report generated: {output}")
    sys.exit(0)


@main.command(name="check-traceability")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def check_traceability(paths: List[str], config: str):
    """Execute spec traceability verification check."""
    report, cfg = _run_checks(paths, config, run_spec=False, run_test=False, run_trace=True, run_adr=False)
    click.echo(report.generate_summary())
    exit_code = determine_exit_code(report.violations, cfg)
    sys.exit(exit_code)


@main.command()
@click.argument("axiom_id")
@click.argument("scope_type", type=click.Choice(["FILE", "DIRECTORY", "COMPONENT"]))
@click.argument("scope_value")
@click.argument("rationale")
@click.option("--created-by", "-u", default="architect-1", help="SSO ID of the architect")
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config")
@click.option("--expires-in-days", "-d", default=90, help="Expiration timeline in days")
@click.option("--permanent", "-p", is_flag=True, help="Make the override permanent")
@click.option("--justification", "-j", default="", help="Elevated Peer Review or signature ID")
def override(
    axiom_id: str,
    scope_type: str,
    scope_value: str,
    rationale: str,
    created_by: str,
    config: str,
    expires_in_days: int,
    permanent: bool,
    justification: str,
):
    """Register a new rule exception override."""
    cfg = load_config(Path(config))
    from .services.override import OverrideService

    try:
        svc = OverrideService(cfg)
        o = svc.create_override(
            axiom_id=axiom_id,
            scope_type=scope_type,
            scope_value=scope_value,
            rationale=rationale,
            created_by=created_by,
            expires_in_days=expires_in_days,
            is_permanent=permanent,
            permanent_justification=justification,
        )
        click.echo(f"Override registered successfully: ID = {o.id}")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error registering override: {e}", err=True)
        sys.exit(3)


@main.command(name="verify-audit-trail")
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def verify_audit_trail(config: str):
    """Verify the cryptographic integrity of the compliance audit trail."""
    cfg = load_config(Path(config))
    from ade_compliance.services.audit import AuditService

    try:
        svc = AuditService(cfg)
        match svc.verify_chain():
            case (True, _):
                click.echo("Success: Compliance audit trail is fully intact and verified.")
                sys.exit(0)
            case (False, errors):
                click.echo("Error: Tampering or chain corruption detected in audit trail!", err=True)
                for err in errors:
                    click.echo(f"  - {err}", err=True)
                sys.exit(1)
    except Exception as e:
        click.echo(f"Error executing verification check: {e}", err=True)
        sys.exit(2)


@main.command(name="prompt-decorate")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def prompt_decorate(paths: List[str], config: str):
    """Retrieve highly structured Markdown prompt block enforcing active constraints."""
    cfg = load_config(Path(config))
    from ade_compliance.utils.prompts import generate_prompt_decorator

    files_list = list(paths) if paths else None
    markdown = generate_prompt_decorator(cfg, files_list)
    click.echo(markdown)
    sys.exit(0)


@main.command(name="install-hook")
def install_hook():
    """Install the git pre-commit hook automatically."""
    try:
        git_root = find_git_root()
        hooks_dir = git_root / ".git" / "hooks"
        if not hooks_dir.exists():
            hooks_dir.mkdir(parents=True, exist_ok=True)

        hook_path = hooks_dir / "pre-commit"
        python_exec = sys.executable.replace("\\", "/")

        hook_content = f"""#!/bin/sh
# Auto-generated by First-ADE compliance framework.
# Dynamic execution matching the current active interpreter context.
"{python_exec}" -m ade_compliance.hooks.pre_commit
"""

        hook_path.write_text(hook_content, encoding="utf-8")

        # On non-Windows platforms, make the hook executable
        if sys.platform != "win32":
            import os
            import stat

            st = os.stat(hook_path)
            os.chmod(hook_path, st.st_mode | stat.S_IEXEC)

        click.echo(f"Success: Git pre-commit hook installed to {hook_path.name}")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error installing pre-commit hook: {e}", err=True)
        sys.exit(2)


@main.command(name="check-deployment")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def check_deployment(paths: List[str], config: str):
    """Check deployment readiness — blocks on unresolved critical/high violations (FR-023)."""
    report, cfg = _run_checks(paths, config, run_spec=True, run_test=True, run_trace=True, run_adr=True)

    from ade_compliance.config import map_severity_to_criticality

    blocking = []
    for v in report.violations:
        criticality = map_severity_to_criticality("critical", v.axiom_id)
        if criticality in ("critical", "high"):
            blocking.append(v)

    if blocking:
        click.echo(f"DEPLOYMENT BLOCKED: {len(blocking)} critical/high violation(s) found.", err=True)
        for v in blocking:
            click.echo(f"  - [{v.axiom_id}] {v.file_path}: {v.message}", err=True)
        sys.exit(1)

    click.echo("Deployment gate passed: No unresolved critical/high violations.")
    sys.exit(0)


def find_git_root() -> Path:
    curr = Path.cwd().resolve()
    for parent in [curr] + list(curr.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Not a git repository (or any of the parent directories): .git")


@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
@click.option("--port", default=8080, type=int, help="Port to bind to (default: 8080)")
def serve(host: str, port: int):
    """Run First-ADE REST API server daemon."""
    from .services.server import run_server

    run_server(host, port)


if __name__ == "__main__":
    main()
