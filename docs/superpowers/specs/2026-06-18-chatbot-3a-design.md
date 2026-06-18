# Core Agentic Chatbot — Design (Step 3a)

**Date:** 2026-06-18
**Status:** Approved
**Scope:** A Streamlit chat page where a user asks air-quality questions in natural
language; a LangGraph ReAct agent (Groq LLM) answers *data* questions by calling the
**deployed** MCP tools, with multi-turn memory.

**NOT in scope** (later sub-projects): RAG knowledge base + router (3b), guardrails
beyond a light system prompt (3c), eval harness (3d), and response streaming (easy
polish later). Claude Desktop is not involved — the chatbot is the only consumer.

## Decisions (made during brainstorming)

- **LLM:** Groq, default model `llama-3.3-70b-versatile` (strong tool-calling, free,
  fast); swappable in config.
- **Agent:** LangGraph prebuilt `create_react_agent` bound to the MCP tools. The custom
  StateGraph router arrives in 3b, where data-vs-RAG routing actually needs it.
- **MCP access:** the live HF endpoint `https://Bhuvandesai-india-air-quality.hf.space/mcp`
  over streamable-HTTP with `Authorization: Bearer <MCP_AUTH_TOKEN>`.

## Components / files

- `chatbot/__init__.py`
- `chatbot/config.py` — load settings from Streamlit secrets / env: `GROQ_API_KEY`,
  `MCP_URL`, `MCP_AUTH_TOKEN`, `MODEL` (default `llama-3.3-70b-versatile`). Fail with a
  clear message if required values are missing. Also exposes `get_logger(name)` with a
  one-time logging config (level from `LOG_LEVEL`, default INFO).
- `chatbot/agent.py` — `build_agent()`:
  - `ChatGroq(model=MODEL, api_key=...)`.
  - Load MCP tools via `langchain_mcp_adapters.client.MultiServerMCPClient({...})` →
    `await client.get_tools()`.
  - `create_react_agent(llm, tools, checkpointer=MemorySaver(), prompt=SYSTEM_PROMPT)`.
- `chatbot/runtime.py` — async↔sync bridge: a persistent background event loop (started
  once, in a daemon thread) with `run(coro)` that submits coroutines to it. The agent +
  MCP tools are created on that loop and reused across Streamlit reruns.
- `pages/Ask_AI.py` — chat UI: `st.chat_message` / `st.chat_input`, `st.session_state`
  for display history and a per-session `thread_id`; builds the agent once via
  `st.cache_resource`; on each user turn calls the agent and renders the reply, plus a
  "Tools used" expander (no emoji anywhere in the UI).
- `chatbot/smoke_chat.py` — headless end-to-end test (no Streamlit).
- `.streamlit/secrets.toml.example` — template; real `secrets.toml` is gitignored.
- `requirements.txt` — add `langgraph`, `langchain-groq`, `langchain-mcp-adapters`,
  `langchain-core`.

## Data flow

```
st.chat_input
  -> append user msg to st.session_state.messages (display)
  -> runtime.run(agent.ainvoke({"messages": [...]},
                                config={"configurable": {"thread_id": <session id>}}))
        ReAct loop: Groq LLM selects an MCP tool
          -> streamable-HTTP call to HF endpoint with bearer header
          -> tool result -> ... -> final answer
  -> render assistant msg
```

## Async↔Streamlit bridge (the main technical risk)

`langchain-mcp-adapters` tools are async-only; Streamlit is synchronous and reruns the
script on every interaction. Using `asyncio.run()` per message creates a new event loop
each call, which breaks cached async MCP tools/connections (cross-loop errors).

**Approach:** one persistent background event loop in a daemon thread (`chatbot/runtime.py`),
created once and cached. The agent and its MCP connection are built on that loop;
`runtime.run(coro)` uses `asyncio.run_coroutine_threadsafe(coro, loop).result()`. This
keeps a single, stable loop for the app's lifetime and is the part to verify first.

## Memory

`MemorySaver` checkpointer keyed by a per-session `thread_id` (UUID stored in
`st.session_state`) so follow-ups ("and the cleanest?") keep context. The display list
in `st.session_state.messages` mirrors the conversation for rendering.

## Observability

Two layers (LangSmith tracing considered and deferred — can be added later via env vars
with zero code change):

1. **Structured Python logging** (always on, no new deps). A `chatbot` logger configured
   once in `config.py`. Per turn, `agent.py`/`runtime.py` log at INFO: the user query,
   each tool call the agent made (name + args), per-call and total latency, and the
   final answer length; errors at ERROR with traceback. This is the primary debugging
   view while building the async bridge and tool loop.
2. **In-UI tool transparency.** After each answer, `pages/Ask_AI.py` renders an
   `st.expander` ("Tools used") listing the MCP tools the agent called with their
   args and latency. No extra plumbing: the tool calls are extracted from the agent's
   returned message history (`AIMessage.tool_calls` + `ToolMessage`s). Makes the agentic
   behaviour visible in the demo.

## System prompt (light scope-setting; real guardrails are 3c)

> You are an assistant for an India air-quality dashboard. Data covers 11 cities,
> 2015–2020, and is historical (not real-time). Use the provided tools for every data
> question; never invent numbers — rely only on tool results. Always report the as-of
> date the data reflects. If asked about a city or date outside coverage, say so. You
> currently answer only air-quality data questions.

## Secrets

Local: `.streamlit/secrets.toml` (gitignored) with `GROQ_API_KEY`, `MCP_AUTH_TOKEN`
(and optionally `MCP_URL`, `MODEL`). Streamlit Cloud: same keys via the app's Secrets
UI. A committed `.streamlit/secrets.toml.example` documents the shape.

## Error handling

- Missing `GROQ_API_KEY` / `MCP_AUTH_TOKEN` → the page shows a clear setup message
  instead of crashing.
- HF Space cold start (free tier sleeps after idle) → first call may take a few seconds;
  show a spinner and a generous client timeout.
- Tool/LLM errors → caught and shown as a friendly assistant message; details logged.

## Verification (Done criteria for 3a)

1. `chatbot/smoke_chat.py` builds the agent with the real Groq key + live MCP endpoint,
   asks "which city has the worst AQI?", and asserts a tool was called and the answer
   names Ahmedabad — proves the whole loop headlessly.
2. `streamlit run app.py` → **Ask AI** page: worst-AQI question (calls `rank_cities`), a
   follow-up that relies on memory, and a compare question (calls `compare_cities`), all
   answered from tool results.

## Watch-outs

- Keep the persistent event loop single and long-lived; do not mix `asyncio.run()`.
- Secrets never committed; only `.example` is.
- Adding the LangChain/LangGraph stack enlarges the dashboard's deploy footprint — fine
  on Streamlit Cloud free tier, but keep deps minimal (no unused extras).
