# validates: FR-001
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from greeter import greet  # noqa: E402


def test_named_caller_is_greeted() -> None:
    assert greet("Ada") == "Hello, Ada."


def test_empty_name_is_refused() -> None:
    with pytest.raises(ValueError):
        greet("")
