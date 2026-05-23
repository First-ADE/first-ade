# implements: FR-017
# traces_to: Π.3.1

"""Centralized Asynchronous Execution Utilities for ADE Compliance.

Provides safe mechanisms to execute asynchronous coroutines from synchronous contexts
without encountering "Event loop is already running" exceptions.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Coroutine


def run_async_safe(coro: Coroutine[Any, Any, Any]) -> Any:
    """Execute an asynchronous coroutine from a synchronous context safely.

    If an event loop is already running in the current thread, this function
    submits the coroutine to be executed in a separate thread using a ThreadPoolExecutor
    and a fresh event loop to block synchronously. Otherwise, it uses asyncio.run().
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: asyncio.run(coro))
            return future.result()
    else:
        return asyncio.run(coro)
