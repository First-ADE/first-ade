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
    # Expand paths (naive)
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(str(path).replace("\\", "/"))
        elif path.is_dir():
            # Recursive .py search for MVP
            for f in path.rglob("*.py"):
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
        sys.exit(1)

    # Output Report
    click.echo(report.generate_summary())

    # Exit code based on violations?
    # For fail-closed, if any violation is NEW/ACKNOWLEDGED (not resolved/overridden) -> exit 1
    # Check strictness logic (warn vs error)
    # MVP: exit 1 if any violations
    if report.violations:
        sys.exit(1)


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
