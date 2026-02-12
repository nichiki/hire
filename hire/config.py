"""Configuration management."""

import copy
import json
from typing import Any

from .paths import get_config_path

# Default configuration
# NOTE: Auto-approve flags are enabled by default for convenience.
# These allow agents to execute actions without manual confirmation.
# Users can customize this in their config file (~/.hire/config.json).
DEFAULT_CONFIG = {
    "adapters": {
        "claude": {
            "command": "claude",
            "args": ["--dangerously-skip-permissions"]
        },
        "codex": {
            "command": "codex",
            "args": ["--full-auto"]
        },
        "gemini": {
            "command": "gemini",
            "args": ["-y"]
        },
        "grok": {
            "model": "grok-4-latest"
        }
    },
    "defaults": {
        "agent": "claude"
    }
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base. Override values take priority."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def load_config() -> dict[str, Any]:
    """Load configuration from file, merged with defaults."""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                user_config = json.load(f)
            return _deep_merge(DEFAULT_CONFIG, user_config)
        except (OSError, json.JSONDecodeError):
            pass
    return copy.deepcopy(DEFAULT_CONFIG)


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_adapter_config(agent: str) -> dict[str, Any]:
    """Get configuration for a specific adapter."""
    config = load_config()
    return config.get("adapters", {}).get(agent, {})
