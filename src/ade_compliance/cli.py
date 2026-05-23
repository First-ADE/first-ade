import asyncio
import sys
from pathlib import Path
from typing import List

import click

from ade_compliance.config import load_config
from ade_compliance.services.orchestrator import Orchestrator


@click.group()
def main():
    """ADE Compliance Framework CLI"""
    pass


@main.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def run(paths: List[str], config: str):
    """Run compliance checks on the specified paths."""
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
        return

    # Load Config
    cfg = load_config(Path(config))

    # Run Orchestrator
    orchestrator = Orchestrator(cfg)

    try:
        report = asyncio.run(orchestrator.run(files))
    except Exception as e:
        click.echo(f"Error running checks: {e}", err=True)
        sys.exit(3)

    # Output Report
    click.echo(report.generate_summary())

    # Exit code based on violations
    if report.violations:
        sys.exit(1)


@main.command(name="check-traceability")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", default=".ade-compliance.yml", help="Path to config file")
def check_traceability(paths: List[str], config: str):
    """Run traceability checks and generate matrix."""
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(str(path).replace("\\", "/"))
        elif path.is_dir():
            for ext in ("*.py", "*.js", "*.ts", "*.tsx", "*.java"):
                for f in path.rglob(ext):
                    files.append(str(f).replace("\\", "/"))

    if not files:
        click.echo("No files found to check.")
        return

    cfg = load_config(Path(config))
    orchestrator = Orchestrator(cfg)

    try:
        report = asyncio.run(orchestrator.run(files))
    except Exception as e:
        click.echo(f"Error running traceability checks: {e}", err=True)
        sys.exit(3)

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
    
    # Exit with code based on traceability violations (Π.3.1)
    trace_violations = [v for v in report.violations if v.axiom_id == "Π.3.1"]
    if trace_violations:
        click.echo(f"\nFound {len(trace_violations)} traceability violation(s):")
        for v in trace_violations:
            click.echo(f"  - {v.file_path}: {v.message}")
        sys.exit(1)
    
    click.echo("\nTraceability check passed successfully!")
    sys.exit(0)


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
