# tests/test_runtime.py
import asyncio
from chatbot import runtime


def test_run_returns_result():
    async def coro():
        await asyncio.sleep(0)
        return 42
    assert runtime.run(coro()) == 42


def test_loop_is_reused():
    async def loop_id():
        return id(asyncio.get_running_loop())
    first = runtime.run(loop_id())
    second = runtime.run(loop_id())
    assert first == second
