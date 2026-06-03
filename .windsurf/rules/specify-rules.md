# first-ade Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-06

## Active Technologies

- Python 3.11+ + Tree-sitter (multi-lang parsing), Click (CLI), FastAPI (HTTP API), Pydantic (data models), SQLAlchemy (audit persistence) (001-ade-compliance)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes

- 001-ade-compliance: Added Python 3.11+ + Tree-sitter (multi-lang parsing), Click (CLI), FastAPI (HTTP API), Pydantic (data models), SQLAlchemy (audit persistence)

<!-- MANUAL ADDITIONS START -->
### Spec Development & Governance
- **Speckit/Specify is Canon**: Speckit (`.specify/` and `specs/`) is the sole, canonical framework for all specification-first, plan-first, and test-first development.
- **Single Source of Truth (SPEC.md)**: The `SPEC.md` file at the root of the project is the official primary specification of the service.
- **Spec Lifecycle**: All new features and changes must start from the parent `SPEC.md` and conclude with their completed details being merged/integrated back into the primary `SPEC.md`.
<!-- MANUAL ADDITIONS END -->
