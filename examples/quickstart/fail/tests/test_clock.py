import datetime


def test_uses_wall_clock() -> None:
    """A test that depends on the real clock is non-deterministic; the forbidden-API engine flags it."""
    assert datetime.datetime.now().year >= 2026
