# tests/test_agent_helpers.py
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from chatbot.agent import extract_tool_calls


def test_extract_tool_calls_reads_ai_tool_calls():
    messages = [
        HumanMessage(content="worst aqi?"),
        AIMessage(
            content="",
            tool_calls=[{"name": "rank_cities",
                         "args": {"metric": "aqi", "n": 1, "order": "desc"},
                         "id": "1"}],
        ),
        ToolMessage(content="{...}", tool_call_id="1"),
        AIMessage(content="Ahmedabad is worst."),
    ]
    calls = extract_tool_calls(messages)
    assert calls == [{"name": "rank_cities",
                      "args": {"metric": "aqi", "n": 1, "order": "desc"}}]


def test_extract_tool_calls_empty_when_none():
    assert extract_tool_calls([AIMessage(content="hi")]) == []


def test_extract_tool_calls_aggregates_across_messages():
    messages = [
        AIMessage(content="", tool_calls=[{"name": "list_cities", "args": {}, "id": "1"}]),
        ToolMessage(content="[...]", tool_call_id="1"),
        AIMessage(content="", tool_calls=[{"name": "get_aqi", "args": {"city": "Delhi"}, "id": "2"}]),
        ToolMessage(content="{...}", tool_call_id="2"),
        AIMessage(content="Done."),
    ]
    calls = extract_tool_calls(messages)
    assert calls == [
        {"name": "list_cities", "args": {}},
        {"name": "get_aqi", "args": {"city": "Delhi"}},
    ]
