# chatbot/smoke_chat.py
"""Headless end-to-end check: build the agent and ask a data question.

Requires GROQ_API_KEY and MCP_AUTH_TOKEN in the environment. Run with:
    GROQ_API_KEY=... MCP_AUTH_TOKEN=... ./.venv/Scripts/python.exe -m chatbot.smoke_chat
"""

import uuid

from chatbot.agent import answer, build_agent


def main() -> None:
    agent = build_agent()
    tid = str(uuid.uuid4())

    r1 = answer(agent, tid, "Which city has the worst AQI right now?")
    print("\nQ1 ->", r1["text"])
    print("tools:", [c["name"] for c in r1["tool_calls"]], "latency:", r1["latency_s"])
    names = [c["name"] for c in r1["tool_calls"]]
    assert names, "expected at least one tool call"
    assert "Ahmedabad" in (r1["text"] or ""), "expected Ahmedabad in the answer"

    r2 = answer(agent, tid, "And which is the cleanest?")
    print("\nQ2 (memory follow-up) ->", r2["text"])
    assert r2["tool_calls"], "expected a tool call on the follow-up"

    print("\nOK: live agent + MCP loop works end to end.")


if __name__ == "__main__":
    main()
