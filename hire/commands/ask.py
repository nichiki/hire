"""Ask command implementation."""

import json
import sys
from argparse import Namespace

from ..adapters import get_adapter
from ..session import (
    create_session,
    find_session,
    get_latest_session,
    list_sessions,
    save_session,
)


def read_stdin() -> str | None:
    """Read from stdin if available (pipe/redirect)."""
    if sys.stdin.isatty():
        return None
    content = sys.stdin.read()
    return content.strip() if content else None


def build_message(message: str | None, stdin: str | None) -> str | None:
    """Build the final message from args and stdin."""
    if message and stdin:
        return f"{message}\n\n--- stdin ---\n{stdin}"
    elif stdin:
        return stdin
    else:
        return message


VALID_TARGETS = {"claude", "codex", "gemini"}


def run_ask(args: Namespace) -> int:
    """Run the ask command."""
    target = args.target
    arg_message = args.message
    stdin_content = read_stdin()
    continue_session = getattr(args, "continue_session", False)
    session_id = args.session
    name = args.name
    model = args.model
    output_json = args.json

    # Handle case where target is actually the message (when target is omitted)
    # e.g., "hire 'message'" -> target='message', message=None
    if target and target not in VALID_TARGETS and arg_message is None:
        arg_message = target
        target = None

    # Build final message from args and stdin
    message = build_message(arg_message, stdin_content)

    # Load config for defaults
    from ..config import load_config
    config = load_config()

    if not target:
        target = config.get("defaults", {}).get("agent")

    # Determine which session to use
    cli_session_id = None
    existing_session = None

    if session_id:
        # Use specified session
        existing_session = find_session(session_id)
        if existing_session:
            cli_session_id = existing_session.get("cli_session_id")
            # If target not specified, get it from session
            if not target:
                target = existing_session.get("agent")
        else:
            print(f"Error: Session not found: {session_id}", file=sys.stderr)
            return 1
    elif name:
        # Check if named session exists
        existing_session = find_session(name)
        if existing_session:
            if continue_session:
                cli_session_id = existing_session.get("cli_session_id")
            # If target not specified, get it from session
            if not target:
                target = existing_session.get("agent")
            # else: create new session with this name (will replace)
    elif continue_session:
        # Continue latest session
        if not target:
            # Try to find latest session across all agents
            sessions = list_sessions()
            if sessions:
                existing_session = sessions[0]
                target = existing_session.get("agent")
        else:
            existing_session = get_latest_session(target)
        
        if existing_session:
            cli_session_id = existing_session.get("cli_session_id")
        else:
            print(f"Warning: No previous session found{' for ' + target if target else ''}, starting new session", file=sys.stderr)

    # Validate target
    if not target:
        print("Error: Target agent is required (claude, codex, or gemini)", file=sys.stderr)
        return 1

    # Validate message
    if not message:
        print("Error: Message is required", file=sys.stderr)
        print("Usage: hire <target> <message>", file=sys.stderr)
        return 1

    # Get the adapter for the target agent
    try:
        adapter = get_adapter(target)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Call the agent
    result = adapter.ask(message, session_id=cli_session_id, model=model)

    if result.get("error"):
        print(f"Error: {result['error']}", file=sys.stderr)
        if result.get("raw"):
            print(f"Raw output: {result['raw']}", file=sys.stderr)
        return 1

    # Get the new session ID from the response
    new_cli_session_id = result.get("session_id")

    # Save or update session
    if existing_session and cli_session_id:
        # Update existing session
        existing_session["cli_session_id"] = new_cli_session_id or cli_session_id
        if name:
            existing_session["name"] = name
        save_session(existing_session)
        session = existing_session
    else:
        # Create new session
        session = create_session(
            agent=target,
            cli_session_id=new_cli_session_id or "unknown",
            name=name,
        )

    # Output
    if output_json:
        output = {
            "response": result.get("response"),
            "session_id": session["id"],
            "cli_session_id": session["cli_session_id"],
            "agent": target,
            "name": session.get("name"),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(result.get("response", ""))

    return 0
