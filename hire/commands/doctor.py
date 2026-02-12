"""Doctor command implementation."""

import copy
import json
import shutil
import sys
from argparse import Namespace

from .. import __version__
from ..adapters.grok import _get_api_key as get_grok_api_key
from ..config import load_config
from ..paths import get_config_path, get_sessions_dir


# CLI-based agents: check binary availability
CLI_AGENTS = {
    "claude": "claude",
    "codex": "codex",
    "gemini": "gemini",
}


def run_doctor(args: Namespace) -> int:
    """Run the doctor command to check environment."""
    print(f"hire-ai v{__version__}")
    print(f"Python {sys.version.split()[0]}")
    print()

    # Check agents
    print("Checking agents...")
    found = 0
    missing = 0

    for name, cmd in CLI_AGENTS.items():
        path = shutil.which(cmd)
        if path:
            print(f"  \u2713 {name} - {path}")
            found += 1
        else:
            print(f"  \u2717 {name} - not found")
            missing += 1

    # Check Grok (API-based)
    if get_grok_api_key():
        print("  \u2713 grok - API key configured")
        found += 1
    else:
        print("  \u2717 grok - API key not found (set api_key in config or GROK_API_KEY env var)")
        missing += 1

    print()

    # Check config
    print("Checking config...")
    config_path = get_config_path()
    if config_path.exists():
        print(f"  \u2713 Config: {config_path}")
    else:
        print(f"  - Config: {config_path} (not created yet, using defaults)")

    sessions_dir = get_sessions_dir()
    session_count = sum(1 for _ in sessions_dir.rglob("*.json"))
    print(f"  \u2713 Sessions: {sessions_dir} ({session_count} sessions)")
    print()

    # Dump effective config (with secrets masked)
    print("Effective config:")
    config = load_config()
    masked = copy.deepcopy(config)
    grok_cfg = masked.get("adapters", {}).get("grok", {})
    if grok_cfg.get("api_key"):
        key = grok_cfg["api_key"]
        grok_cfg["api_key"] = key[:8] + "..." if len(key) > 8 else "***"
    print(json.dumps(masked, indent=2, ensure_ascii=False))
    print()

    # Summary
    if missing == 0:
        print("All good!")
    elif found == 0:
        print("No agents found. Install at least one of: claude, codex, gemini, grok")
        return 1
    else:
        print(f"Ready! ({missing} agent(s) not installed)")

    return 0
