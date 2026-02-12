"""Agent adapters."""

from .base import AgentAdapter
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .gemini import GeminiAdapter
from .grok import GrokAdapter


def get_adapter(agent: str) -> AgentAdapter:
    """Get an adapter for the specified agent."""
    adapters = {
        "claude": ClaudeAdapter,
        "codex": CodexAdapter,
        "gemini": GeminiAdapter,
        "grok": GrokAdapter,
    }
    if agent not in adapters:
        raise ValueError(f"Unknown agent: {agent}. Available: {list(adapters.keys())}")
    return adapters[agent]()


__all__ = ["AgentAdapter", "ClaudeAdapter", "CodexAdapter", "GeminiAdapter", "GrokAdapter", "get_adapter"]
