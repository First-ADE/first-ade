# implements: FR-026
# traces_to: Π.3.1

import sys

from loguru import logger

# Remove default unformatted console logger
logger.remove()

# Register structured JSON logger to stdout
logger.add(sys.stdout, serialize=True)
