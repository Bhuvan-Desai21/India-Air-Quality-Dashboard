# chatbot/config.py
"""Environment-based settings and logging for the chatbot package."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

DEFAULT_MCP_URL = "https://Bhuvandesai-india-air-quality.hf.space/mcp"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


@dataclass(frozen=True)
class Settings:
    groq_api_key: str  # validated here; ChatGroq reads it from the env directly
    mcp_auth_token: str
    mcp_url: str
    model: str


def get_settings() -> Settings:
    """Read settings from the environment, raising if required values are missing."""
    missing = [k for k in ("GROQ_API_KEY", "MCP_AUTH_TOKEN") if not os.environ.get(k)]
    if missing:
        raise RuntimeError(
            "Missing required settings: " + ", ".join(missing)
            + ". Set them in .streamlit/secrets.toml or the environment."
        )
    return Settings(
        groq_api_key=os.environ["GROQ_API_KEY"],
        mcp_auth_token=os.environ["MCP_AUTH_TOKEN"],
        mcp_url=os.environ.get("MCP_URL", DEFAULT_MCP_URL),
        model=os.environ.get("MODEL", DEFAULT_MODEL),
    )


_LOG_CONFIGURED = False


def get_logger(name: str = "chatbot") -> logging.Logger:
    """Return a logger, configuring the root handler once at LOG_LEVEL (default INFO)."""
    global _LOG_CONFIGURED
    if not _LOG_CONFIGURED:
        logging.basicConfig(
            level=os.environ.get("LOG_LEVEL", "INFO"),
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        _LOG_CONFIGURED = True
    return logging.getLogger(name)
