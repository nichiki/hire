"""Doctor command implementation."""

import shutil
import sys
from argparse import Namespace

from .. import __version__
from ..paths import get_config_path, get_sessions_dir


AGENTS = {
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
    for name, cmd in AGENTS.items():
        path = shutil.which(cmd)
        if path:
            print(f"  \u2713 {name} - {path}")
            found += 1
        else:
            print(f"  \u2717 {name} - not found")
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

    # Summary
    if missing == 0:
        print("All good!")
    elif found == 0:
        print("No agents found. Install at least one of: claude, codex, gemini")
        return 1
    else:
        print(f"Ready! ({missing} agent(s) not installed)")

    return 0
