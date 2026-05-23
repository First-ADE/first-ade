import sys

from loguru import logger

# Remove default unformatted console logger
logger.remove()

# Register structured JSON logger to stdout
logger.add(sys.stdout, serialize=True)
