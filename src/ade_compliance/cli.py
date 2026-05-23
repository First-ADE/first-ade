import asyncio
import sys
from pathlib import Path
from typing import List, Tuple

import click

from ade_compliance.config import Config, get_axiom_strictness, load_config
from ade_compliance.models.report import ComplianceReport
from ade_compliance.services.orchestrator import Orchestrator


def determine_exit_code(violations: List, config: Config) -> int:
    """Map violations and strictness levels to exit codes:
    - 0: Compliant (or all violations are 'audit')
    - 1: Violations detected (at least one 'enforce' strictness)
    - 2: Warnings detected (no 'enforce', at least one 'warn' strictness)
    - 3: Internal framework error
    """
    if not violations:
        return 0

    has_enforce = False
    has_warn = False

    for v in violations:
        axiom_id = v.axiom_id or ""
        strictness = get_axiom_strictness(config, axiom_id)

        if strictness == "enforce":
            has_enforce = True
        elif strictness == "warn":
            has_warn = True

    if has_enforce:
        return 1
    if has_warn:
        return 2

    return 0


def _run_checks(
    paths: List[str],
    config: str,
    run_spec: bool = True,
    run_test: bool = True,
    run_trace: bool = True,
    run_adr: bool = True,
) -> Tuple[ComplianceReport, Config]:
    # Expand paths
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(str(path).replace("\\", "/"))
        elif path.is_dir():
            # Recursive search for supported languages
            for ext in ("*.py", "*.js", "*.ts", "*.tsx", "*.java"):
                for f in path.rglob(ext):
                    files.append(str(f).replace("\\", "/"))

    if not files:
        click.echo("No files found to check.")
        sys.exit(0)

    # Load Config
    cfg = load_config(Path(config))

    # Configure active engines
    cfg.engines.spec.enabled = cfg.engines.spec.enabled and run_spec
    cfg.engines.test.enabled = cfg.engines.test.enabled and run_test
    cfg.engines.trace.enabled = cfg.engines.trace.enabled and run_trace
    if hasattr(cfg.engines, "adr"):
        cfg.engines.adr.enabled = cfg.engines.adr.enabled and run_adr

    # Run Orchestrator
    orchestrator = Orchestrator(cfg)

    try:
        report = asyncio.run(orchestrator.run(files))
    except Exception as e:
        click.echo(f"Error running checks: {e}", err=True)
        sys.exit(3)

    return report, cfg


@click.group()
def main():
    """ADE Compliance Framework CLI"""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


@main.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def run(paths: List[str], config: str):
    """Run compliance checks on the specified paths (legacy compatibility)."""
    report, cfg = _run_checks(paths, config, run_spec=True, run_test=True, run_trace=True, run_adr=True)
    click.echo(report.generate_summary())
    if report.violations:
        sys.exit(1)
    sys.exit(0)


@main.command(name="check-all")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def check_all(paths: List[str], config: str):
    """Run all compliance checks on the specified paths."""
    report, cfg = _run_checks(paths, config, run_spec=True, run_test=True, run_trace=True, run_adr=True)
    click.echo(report.generate_summary())
    exit_code = determine_exit_code(report.violations, cfg)
    sys.exit(exit_code)


@main.command(name="check-spec")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def check_spec(paths: List[str], config: str):
    """Run specification compliance checks."""
    report, cfg = _run_checks(paths, config, run_spec=True, run_test=False, run_trace=False, run_adr=False)
    click.echo(report.generate_summary())
    exit_code = determine_exit_code(report.violations, cfg)
    sys.exit(exit_code)


@main.command(name="check-test")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def check_test(paths: List[str], config: str):
    """Run test compliance checks."""
    report, cfg = _run_checks(paths, config, run_spec=False, run_test=True, run_trace=False, run_adr=False)
    click.echo(report.generate_summary())
    exit_code = determine_exit_code(report.violations, cfg)
    sys.exit(exit_code)


@main.command(name="check-traceability")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def check_traceability(paths: List[str], config: str):
    """Run traceability checks and generate matrix."""
    report, cfg = _run_checks(paths, config, run_spec=False, run_test=False, run_trace=True, run_adr=False)

    # Print Traceability Matrix
    click.echo("\n--- Traceability Matrix ---")
    if not report.traceability_matrix:
        click.echo("No traceability links extracted.")
    else:
        for source, links in report.traceability_matrix.items():
            click.echo(f"\nSource: {source}")
            for ltype, targets in links.items():
                if targets:
                    click.echo(f"  {ltype.capitalize()}: {', '.join(targets)}")

    trace_violations = [v for v in report.violations if v.axiom_id == "Π.3.1"]
    if trace_violations:
        click.echo(f"\nFound {len(trace_violations)} traceability violation(s):")
        for v in trace_violations:
            click.echo(f"  - {v.file_path}: {v.message}")
        exit_code = determine_exit_code(trace_violations, cfg)
        sys.exit(exit_code)

    click.echo("\nTraceability check passed successfully!")
    sys.exit(0)


@main.command(name="check-adr")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def check_adr(paths: List[str], config: str):
    """Run ADR compliance and architectural change checks."""
    report, cfg = _run_checks(paths, config, run_spec=False, run_test=False, run_trace=False, run_adr=True)
    click.echo(report.generate_summary())
    exit_code = determine_exit_code(report.violations, cfg)
    sys.exit(exit_code)


@main.command(name="generate-report")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def generate_report(paths: List[str], config: str):
    """Generate machine-readable JSON compliance report."""
    report, cfg = _run_checks(paths, config, run_spec=True, run_test=True, run_trace=True, run_adr=True)
    report.generate_summary()
    click.echo(report.model_dump_json(by_alias=True))
    exit_code = determine_exit_code(report.violations, cfg)
    sys.exit(exit_code)


@main.command(name="override")
@click.argument("axiom_id")
@click.option(
    "--scope-type",
    "-s",
    type=click.Choice(["FILE", "DIRECTORY", "COMPONENT"]),
    default="FILE",
    help="Override scope type",
)
@click.option("--scope-value", "-v", required=True, help="File path, directory path, or component name")
@click.option("--rationale", "-r", required=True, help="Rationale for the override (min 20 characters)")
@click.option("--created-by", "-b", required=True, help="Architect SSO ID")
@click.option("--expires-in-days", "-e", type=int, default=90, help="Override expiration in days")
@click.option("--permanent", is_flag=True, help="Make the override permanent")
@click.option("--justification", "-j", default="", help="Permanent justification (required if permanent)")
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def override(
    axiom_id, scope_type, scope_value, rationale, created_by, expires_in_days, permanent, justification, config
):
    """Create a compliance violation override."""
    if len(rationale) < 20:
        click.echo("Error: Rationale must be at least 20 characters long.", err=True)
        sys.exit(3)
    if permanent and not justification:
        click.echo("Error: Permanent justification is required when is_permanent is True.", err=True)
        sys.exit(3)

    cfg = load_config(Path(config))
    from ade_compliance.services.override import OverrideService

    try:
        svc = OverrideService(cfg)
        res = svc.create_override(
            axiom_id=axiom_id,
            scope_type=scope_type,
            scope_value=scope_value,
            rationale=rationale,
            created_by=created_by,
            expires_in_days=expires_in_days,
            is_permanent=permanent,
            permanent_justification=justification,
        )
        click.echo(f"Override created successfully: ID {res.id}")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error creating override: {e}", err=True)
        sys.exit(3)


@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
@click.option("--port", default=8080, type=int, help="Port to bind to (default: 8080)")
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def serve(host: str, port: int, config: str):
    """Start the ADE Compliance HTTP API server."""
    import uvicorn

    click.echo(f"Starting ADE Compliance server on {host}:{port}")
    uvicorn.run(
        "ade_compliance.server:app",
        host=host,
        port=port,
        workers=1,
        log_level="info",
    )


if __name__ == "__main__":
    main()
