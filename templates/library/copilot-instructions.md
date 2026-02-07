# {{project_name}} — GitHub Copilot Instructions

## Project Context

**AXIOM ACCEPTANCE**: You must accept the [ADE Core Axioms](https://github.com/First-ADE/.github/blob/main/docs/AXIOMS.md) before assisting. All suggestions must align with these axioms.

This is a Python library following **Axiom Driven Engineering (ADE)** principles.

## Code Style

- Use type annotations on all functions
- Prefer `async`/`await` for I/O operations
- Follow single responsibility principle
- Keep functions small and focused

## Testing

- Write tests BEFORE implementation (TDD)
- Use pytest with pytest-asyncio for async tests
- Target ≥80% coverage on core logic

## File Patterns

```python
# src/{{project_name}}/models.py
from dataclasses import dataclass

@dataclass
class ExampleModel:
    """Model documentation."""
    field: str
```

```python
# tests/test_models.py
import pytest
from {{project_name}}.models import ExampleModel

def test_example_model():
    """Test description."""
    model = ExampleModel(field="value")
    assert model.field == "value"
```

## Imports

```python
# Standard library
from typing import Optional

# Third-party
import pytest

# Local
from {{project_name}} import core
```

## Commit Messages

```
type(scope): description

Types: feat, fix, test, refactor, docs, chore
```

## Spec References

Check `.specify/specs/` before implementing new features.

## ADR References

Check `docs/decisions/` before making architectural decisions.
