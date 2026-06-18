# tests/test_config.py
import pytest
from chatbot import config


def test_missing_required_raises_listing_keys(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
    with pytest.raises(RuntimeError) as exc:
        config.get_settings()
    msg = str(exc.value)
    assert "GROQ_API_KEY" in msg and "MCP_AUTH_TOKEN" in msg


def test_defaults_and_values(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_x")
    monkeypatch.setenv("MCP_AUTH_TOKEN", "tok")
    monkeypatch.delenv("MCP_URL", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    s = config.get_settings()
    assert s.groq_api_key == "gsk_x"
    assert s.mcp_auth_token == "tok"
    assert s.model == "llama-3.3-70b-versatile"
    assert s.mcp_url.endswith("/mcp")
