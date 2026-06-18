# chatbot/agent.py
"""Builds the LangGraph ReAct agent over the deployed MCP tools, and runs turns."""

from __future__ import annotations

import time
from typing import Any

from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from chatbot import runtime
from chatbot.config import get_logger, get_settings

log = get_logger("chatbot.agent")

# Metadata (name + description) for the tools currently loaded from the MCP server,
# populated by build_agent() and surfaced in the UI "how this works" panel.
TOOLS_INFO: list[dict] = []


def tools_info() -> list[dict]:
    """Return [{name, description}] for the loaded MCP tools (empty until built)."""
    return list(TOOLS_INFO)


SYSTEM_PROMPT = (
    "You are an assistant for an India air-quality dashboard. Data covers 11 cities, "
    "2015-2020, and is historical (not real-time). Use the provided tools for every "
    "data question; never invent numbers - rely only on tool results. Always report "
    "the as-of date the data reflects. If asked about a city or date outside coverage, "
    "say so. You currently answer only air-quality data questions."
)


def extract_tool_calls(messages: list) -> list[dict]:
    """Pull the tool calls the agent made out of a message list."""
    calls = []
    for m in messages:
        for tc in getattr(m, "tool_calls", None) or []:
            calls.append({"name": tc["name"], "args": tc.get("args", {})})
    return calls


def current_turn(messages: list) -> list:
    """Return only the latest turn's messages (those after the last human message).

    With a MemorySaver checkpointer, ainvoke returns the whole thread history; we want
    just this turn so the answer text and "tools used" reflect the current question,
    not earlier ones.
    """
    last_human = -1
    for i, m in enumerate(messages):
        if getattr(m, "type", None) == "human":
            last_human = i
    return messages[last_human + 1:]


def build_agent() -> Any:
    """Build the ReAct agent bound to the MCP tools. Runs on the shared loop."""
    s = get_settings()
    # get_settings() guarantees GROQ_API_KEY is in the environment; ChatGroq reads it
    # from there, which avoids api_key/groq_api_key param-name differences across versions.
    llm = ChatGroq(model=s.model, temperature=0)
    client = MultiServerMCPClient({
        "air_quality": {
            "transport": "streamable_http",
            "url": s.mcp_url,
            "headers": {"Authorization": f"Bearer {s.mcp_auth_token}"},
        }
    })
    try:
        tools = runtime.run(client.get_tools())
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Failed to load MCP tools from {s.mcp_url}: {e}") from e
    log.info("Loaded %d MCP tools: %s", len(tools), [t.name for t in tools])
    TOOLS_INFO.clear()
    TOOLS_INFO.extend(
        {"name": t.name, "description": (getattr(t, "description", "") or "").strip()}
        for t in tools
    )
    return create_react_agent(llm, tools, checkpointer=MemorySaver(), prompt=SYSTEM_PROMPT)


def answer(agent: Any, thread_id: str, user_text: str) -> dict[str, Any]:
    """Run one user turn. Returns {text, tool_calls, latency_s}."""
    log.info("Q[%s]: %s", thread_id, user_text)
    start = time.perf_counter()
    result = runtime.run(agent.ainvoke(
        {"messages": [{"role": "user", "content": user_text}]},
        config={"configurable": {"thread_id": thread_id}},
    ))
    latency = round(time.perf_counter() - start, 2)
    turn = current_turn(result["messages"])
    text = (turn[-1].content if turn else "") or ""
    tool_calls = extract_tool_calls(turn)
    log.info("A[%s] (%.2fs, tools=%s): %d chars",
             thread_id, latency, [c["name"] for c in tool_calls], len(text or ""))
    return {"text": text, "tool_calls": tool_calls, "latency_s": latency}
