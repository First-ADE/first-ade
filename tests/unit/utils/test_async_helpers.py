# implements: FR-002
# traces_to: Π.2.1

import asyncio
from ade_compliance.utils.async_helpers import run_async_safe


def test_run_async_safe_no_loop():
    async def dummy():
        return 42

    res = run_async_safe(dummy())
    assert res == 42


def test_run_async_safe_with_running_loop():
    async def outer():
        async def inner():
            await asyncio.sleep(0.01)
            return 99
        
        # run_async_safe should run the inner coro in a separate thread/loop safely
        return run_async_safe(inner())

    res = asyncio.run(outer())
    assert res == 99
