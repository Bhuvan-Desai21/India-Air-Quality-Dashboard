# chatbot/runtime.py
"""Persistent background event loop bridging async MCP tools to sync Streamlit.

asyncio.run() per call would create a new loop each time and break cached async
MCP tools/connections (cross-loop errors). Instead we keep one loop alive in a
daemon thread for the app's lifetime and submit coroutines to it.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Coroutine

# Bound every call so a slow/unresponsive MCP endpoint cannot hang a Streamlit worker
# thread forever. Generous enough for a cold Hugging Face Space start plus a few tool calls.
DEFAULT_TIMEOUT = 120.0


class _BackgroundLoop:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def run(self, coro: Coroutine, timeout: float | None) -> Any:
        # Raises concurrent.futures.TimeoutError if the coroutine exceeds `timeout`.
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout)


_RUNNER: _BackgroundLoop | None = None
_LOCK = threading.Lock()


def get_runner() -> _BackgroundLoop:
    global _RUNNER
    if _RUNNER is None:
        with _LOCK:
            if _RUNNER is None:
                _RUNNER = _BackgroundLoop()
    return _RUNNER


def run(coro: Coroutine, timeout: float | None = DEFAULT_TIMEOUT) -> Any:
    """Run a coroutine on the shared background loop and return its result.

    Blocks up to `timeout` seconds; raises concurrent.futures.TimeoutError otherwise.
    """
    return get_runner().run(coro, timeout)
