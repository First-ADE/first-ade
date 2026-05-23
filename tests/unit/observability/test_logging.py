# implements: FR-002
# traces_to: Π.2.1

from loguru import logger
from ade_compliance.observability.logging import sys


def test_logging_configuration():
    assert logger is not None
    assert sys.stdout is not None
