"""Wait for the HF Space rebuild to finish, then verify 11 MCP tools are live.

Polls space runtime stage until the new build is RUNNING (not _BUILDING), then
connects to the deployed streamable-HTTP /mcp endpoint with the bearer token and
lists the tools. One-off deploy check.
"""

from __future__ import annotations

import asyncio
import time
import tomllib
from pathlib import Path

from huggingface_hub import HfApi
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

REPO = "Bhuvandesai/india-air-quality"
MCP_URL = "https://Bhuvandesai-india-air-quality.hf.space/mcp"


def _token() -> str:
    secrets = tomllib.loads(
        (Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml").read_text()
    )
    return secrets["MCP_AUTH_TOKEN"]


def wait_for_build(timeout_s: int = 420) -> str:
    api = HfApi()
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        rt = api.space_info(repo_id=REPO).runtime
        stage = rt.stage if rt else "UNKNOWN"
        if stage != last:
            print(f"  stage: {stage}", flush=True)
            last = stage
        if stage == "RUNNING":
            return stage
        if stage in ("BUILD_ERROR", "RUNTIME_ERROR", "CONFIG_ERROR"):
            raise SystemExit(f"Space build failed: {stage}")
        time.sleep(12)
    raise SystemExit("Timed out waiting for build")


async def list_tools(token: str) -> list[str]:
    headers = {"Authorization": f"Bearer {token}"}
    async with streamablehttp_client(MCP_URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools()
            return sorted(t.name for t in resp.tools)


def main() -> None:
    wait_for_build()
    # The new container needs a moment to accept connections after RUNNING.
    time.sleep(8)
    token = _token()
    names = asyncio.run(list_tools(token))
    print(f"\nLIVE TOOLS ({len(names)}):")
    for n in names:
        print(" ", n)
    assert len(names) == 11, f"expected 11 tools, got {len(names)}"
    print("\nDEPLOY VERIFIED: 11 tools live.")


if __name__ == "__main__":
    main()
