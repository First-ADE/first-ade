# implements: FR-015
# traces_to: Π.2.2

"""Unit tests for the ForbiddenAPIEngine — TDD Red Phase.

Validates AST-based detection of forbidden API calls in Python test suites,
enforcing test determinism per FR-015 and Principle III.
"""

import textwrap

import pytest

from ade_compliance.config import EngineConfig
from ade_compliance.engines.forbidden_api_engine import ForbiddenAPIEngine


@pytest.fixture
def engine():
    """Create a ForbiddenAPIEngine with enforcement enabled."""
    config = EngineConfig(enabled=True, strictness="enforce")
    return ForbiddenAPIEngine(config)


@pytest.fixture
def disabled_engine():
    """Create a ForbiddenAPIEngine with engine disabled."""
    config = EngineConfig(enabled=False, strictness="enforce")
    return ForbiddenAPIEngine(config)


# --------------------------------------------------------------------------
# 1. time.sleep detection
# --------------------------------------------------------------------------
class TestTimeSleepDetection:
    """Verify time.sleep() calls are flagged in test files."""

    def test_detect_time_sleep_direct(self, engine):
        """Direct time.sleep(1) call in test file should produce a violation."""
        code = textwrap.dedent("""\
            import time

            def test_something():
                time.sleep(1)
                assert True
        """)
        violations = engine.scan_source(code, "tests/test_example.py")
        assert len(violations) >= 1
        sleep_violations = [v for v in violations if "time.sleep" in v.message]
        assert len(sleep_violations) == 1
        assert sleep_violations[0].axiom_id == "Π.2.2"
        assert sleep_violations[0].severity.value == "critical"

    def test_detect_time_sleep_from_import(self, engine):
        """from time import sleep; sleep(5) should also be detected."""
        code = textwrap.dedent("""\
            from time import sleep

            def test_wait():
                sleep(5)
        """)
        violations = engine.scan_source(code, "tests/test_wait.py")
        sleep_violations = [v for v in violations if "sleep" in v.message.lower()]
        assert len(sleep_violations) >= 1


# --------------------------------------------------------------------------
# 2. datetime.now / datetime.utcnow detection
# --------------------------------------------------------------------------
class TestDatetimeDetection:
    """Verify datetime.now() and datetime.utcnow() are flagged."""

    def test_detect_datetime_now(self, engine):
        """datetime.now() without mocking should produce a violation."""
        code = textwrap.dedent("""\
            from datetime import datetime

            def test_timestamp():
                ts = datetime.now()
                assert ts is not None
        """)
        violations = engine.scan_source(code, "tests/test_ts.py")
        dt_violations = [v for v in violations if "datetime.now" in v.message]
        assert len(dt_violations) >= 1
        assert dt_violations[0].axiom_id == "Π.2.2"

    def test_detect_datetime_utcnow(self, engine):
        """datetime.utcnow() should also be flagged."""
        code = textwrap.dedent("""\
            import datetime

            def test_utc():
                now = datetime.datetime.utcnow()
        """)
        violations = engine.scan_source(code, "tests/test_utc.py")
        utc_violations = [v for v in violations if "utcnow" in v.message]
        assert len(utc_violations) >= 1


# --------------------------------------------------------------------------
# 3. Unseeded random detection
# --------------------------------------------------------------------------
class TestRandomDetection:
    """Verify unseeded random.* calls are flagged."""

    def test_detect_unseeded_random(self, engine):
        """random.randint() without preceding random.seed() should be flagged."""
        code = textwrap.dedent("""\
            import random

            def test_dice():
                result = random.randint(1, 6)
                assert 1 <= result <= 6
        """)
        violations = engine.scan_source(code, "tests/test_dice.py")
        rng_violations = [v for v in violations if "random" in v.message.lower()]
        assert len(rng_violations) >= 1
        assert rng_violations[0].axiom_id == "Π.2.2"

    def test_allow_seeded_random(self, engine):
        """random.randint() AFTER random.seed() should NOT be flagged."""
        code = textwrap.dedent("""\
            import random

            def test_deterministic_dice():
                random.seed(42)
                result = random.randint(1, 6)
                assert result == 6
        """)
        violations = engine.scan_source(code, "tests/test_seeded.py")
        rng_violations = [v for v in violations if "random" in v.message.lower()]
        assert len(rng_violations) == 0

    def test_detect_random_choice(self, engine):
        """random.choice() without seed should be flagged."""
        code = textwrap.dedent("""\
            import random

            def test_pick():
                item = random.choice([1, 2, 3])
                assert item in [1, 2, 3]
        """)
        violations = engine.scan_source(code, "tests/test_choice.py")
        rng_violations = [v for v in violations if "random" in v.message.lower()]
        assert len(rng_violations) >= 1

    def test_detect_random_shuffle(self, engine):
        """random.shuffle() without seed should be flagged."""
        code = textwrap.dedent("""\
            import random

            def test_shuffle():
                items = [1, 2, 3]
                random.shuffle(items)
        """)
        violations = engine.scan_source(code, "tests/test_shuffle.py")
        rng_violations = [v for v in violations if "random" in v.message.lower()]
        assert len(rng_violations) >= 1


# --------------------------------------------------------------------------
# 4. Network I/O detection
# --------------------------------------------------------------------------
class TestNetworkIODetection:
    """Verify direct network calls are flagged in test files."""

    def test_detect_requests_get(self, engine):
        """requests.get() in tests should be flagged."""
        code = textwrap.dedent("""\
            import requests

            def test_api():
                resp = requests.get("https://example.com")
                assert resp.status_code == 200
        """)
        violations = engine.scan_source(code, "tests/test_api.py")
        net_violations = [v for v in violations if "requests" in v.message.lower()]
        assert len(net_violations) >= 1

    def test_detect_httpx_post(self, engine):
        """httpx.post() in tests should be flagged."""
        code = textwrap.dedent("""\
            import httpx

            def test_submit():
                resp = httpx.post("https://example.com/api", json={})
        """)
        violations = engine.scan_source(code, "tests/test_httpx.py")
        net_violations = [v for v in violations if "httpx" in v.message.lower()]
        assert len(net_violations) >= 1


# --------------------------------------------------------------------------
# 5. os.system detection
# --------------------------------------------------------------------------
class TestSubprocessDetection:
    """Verify os.system() calls are flagged."""

    def test_detect_os_system(self, engine):
        """os.system() in tests should be flagged."""
        code = textwrap.dedent("""\
            import os

            def test_exec():
                os.system("echo hello")
        """)
        violations = engine.scan_source(code, "tests/test_exec.py")
        os_violations = [v for v in violations if "os.system" in v.message]
        assert len(os_violations) >= 1


# --------------------------------------------------------------------------
# 6. Clean file — no violations
# --------------------------------------------------------------------------
class TestCleanFile:
    """Verify clean test files produce no violations."""

    def test_clean_test_file(self, engine):
        """A test file with no forbidden calls should produce zero violations."""
        code = textwrap.dedent("""\
            def test_addition():
                assert 1 + 1 == 2

            def test_string():
                assert "hello".upper() == "HELLO"
        """)
        violations = engine.scan_source(code, "tests/test_clean.py")
        assert len(violations) == 0

    def test_clean_with_mocked_time(self, engine):
        """Using unittest.mock to patch time should NOT trigger violations."""
        code = textwrap.dedent("""\
            from unittest.mock import patch

            def test_mocked_time():
                with patch("time.sleep"):
                    pass
        """)
        violations = engine.scan_source(code, "tests/test_mocked.py")
        sleep_violations = [v for v in violations if "time.sleep" in v.message]
        assert len(sleep_violations) == 0


# --------------------------------------------------------------------------
# 7. Non-test files skipped
# --------------------------------------------------------------------------
class TestFileFiltering:
    """Verify non-test files are skipped by the async check method."""

    @pytest.mark.asyncio
    async def test_src_files_skipped(self, engine):
        """Files in src/ should NOT be checked for forbidden APIs."""
        # The async check() method should skip src/ files
        violations = await engine.check(["src/ade_compliance/services/audit.py"])
        assert len(violations) == 0

    @pytest.mark.asyncio
    async def test_only_python_files_checked(self, engine):
        """Non-Python files should be skipped."""
        violations = await engine.check(["tests/test_example.js"])
        assert len(violations) == 0


# --------------------------------------------------------------------------
# 8. Engine disabled
# --------------------------------------------------------------------------
class TestEngineDisabled:
    """Verify engine respects enabled=False config."""

    @pytest.mark.asyncio
    async def test_disabled_engine_returns_empty(self, disabled_engine):
        """A disabled engine should always return an empty list."""
        violations = await disabled_engine.check(["tests/test_something.py"])
        assert violations == []


# --------------------------------------------------------------------------
# 9. Malformed Python file
# --------------------------------------------------------------------------
class TestMalformedFile:
    """Verify graceful handling of syntax errors."""

    def test_syntax_error_returns_empty(self, engine):
        """A file with Python syntax errors should be skipped gracefully."""
        code = "def test_broken(\n    assert True\n"
        violations = engine.scan_source(code, "tests/test_broken.py")
        assert violations == []


# --------------------------------------------------------------------------
# 10. Violation metadata
# --------------------------------------------------------------------------
class TestViolationMetadata:
    """Verify violation objects have correct metadata."""

    def test_violation_has_correct_axiom(self, engine):
        """All violations should reference axiom Π.2.2."""
        code = textwrap.dedent("""\
            import time
            def test_x():
                time.sleep(1)
        """)
        violations = engine.scan_source(code, "tests/test_meta.py")
        for v in violations:
            assert v.axiom_id == "Π.2.2"

    def test_violation_has_correct_file_path(self, engine):
        """Violation file_path should match the file being scanned."""
        code = textwrap.dedent("""\
            import time
            def test_x():
                time.sleep(1)
        """)
        violations = engine.scan_source(code, "tests/unit/test_meta.py")
        for v in violations:
            assert v.file_path == "tests/unit/test_meta.py"

    def test_violation_message_includes_line_number(self, engine):
        """Violation message should include the line number of the forbidden call."""
        code = textwrap.dedent("""\
            import time

            def test_x():
                time.sleep(1)
        """)
        violations = engine.scan_source(code, "tests/test_line.py")
        sleep_violations = [v for v in violations if "time.sleep" in v.message]
        assert len(sleep_violations) == 1
        # Line 4 contains time.sleep(1)
        assert "line 4" in sleep_violations[0].message.lower()
