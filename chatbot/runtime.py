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


class _BackgroundLoop:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def run(self, coro: Coroutine) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()


_RUNNER: _BackgroundLoop | None = None
_LOCK = threading.Lock()


def get_runner() -> _BackgroundLoop:
    global _RUNNER
    if _RUNNER is None:
        with _LOCK:
            if _RUNNER is None:
                _RUNNER = _BackgroundLoop()
    return _RUNNER


def run(coro: Coroutine) -> Any:
    """Run a coroutine on the shared background loop and return its result."""
    return get_runner().run(coro)
