# implements: FR-001
# traces_to: FR-001-greeter.md


def greet(name: str) -> str:
    """Return a greeting for a non-empty name; refuse an empty one."""
    if not name:
        raise ValueError("name must not be empty")
    return f"Hello, {name}."
