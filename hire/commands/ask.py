"""Ask command implementation."""

import json
import sys
from argparse import Namespace

from ..adapters import get_adapter
from ..clipboard import copy_to_clipboard
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


VALID_TARGETS = {"claude", "codex", "gemini", "grok"}


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
    copy_clip = getattr(args, "clip", False)
    out_file = getattr(args, "out", None)

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

    # Determine which session to use
    cli_session_id = None
    existing_session = None

    if session_id:
        # Use specified session
        try:
            existing_session = find_session(session_id)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        if existing_session:
            cli_session_id = existing_session.get("cli_session_id")
            # When resuming a session, always use the session's agent
            if not target:
                target = existing_session.get("agent")
        else:
            print(f"Error: Session not found: {session_id}", file=sys.stderr)
            return 1
    elif name:
        # Check if named session exists
        try:
            existing_session = find_session(name)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
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

    # Fall back to default agent if not specified
    if not target:
        target = config.get("defaults", {}).get("agent")

    # Validate target
    if not target:
        print("Error: Target agent is required (claude, codex, gemini, or grok)", file=sys.stderr)
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

    # Load conversation history for Grok sessions
    history = None
    if target == "grok" and existing_session:
        history = existing_session.get("messages", [])

    # For Grok, parse @filepath references and extract files
    file_paths = None
    if target == "grok":
        from ..files import extract_file_refs
        message, file_paths = extract_file_refs(message)

    # Call the agent
    if target == "grok":
        result = adapter.ask(message, session_id=cli_session_id, model=model,
                             history=history, files=file_paths or None)
    else:
        result = adapter.ask(message, session_id=cli_session_id, model=model)

    if result.get("error"):
        print(f"Error: {result['error']}", file=sys.stderr)
        if result.get("raw"):
            print(f"Raw output: {result['raw']}", file=sys.stderr)
        return 1

    # Get the new session ID from the response
    new_cli_session_id = result.get("session_id")

    # Build updated message history for Grok
    if target == "grok":
        updated_messages = list(history) if history else []
        updated_messages.append({"role": "user", "content": message})
        if result.get("response"):
            updated_messages.append({"role": "assistant", "content": result["response"]})

    # Save or update session
    if existing_session and cli_session_id:
        # Update existing session
        existing_session["cli_session_id"] = new_cli_session_id or cli_session_id
        if name:
            existing_session["name"] = name
        if target == "grok":
            existing_session["messages"] = updated_messages
        save_session(existing_session)
        session = existing_session
    else:
        # Create new session
        session = create_session(
            agent=target,
            cli_session_id=new_cli_session_id or "unknown",
            name=name,
        )
        if target == "grok":
            session["messages"] = updated_messages
            save_session(session)

    # Output
    if output_json:
        output = {
            "response": result.get("response"),
            "session_id": session["id"],
            "cli_session_id": session["cli_session_id"],
            "agent": target,
            "name": session.get("name"),
        }
        output_text = json.dumps(output, indent=2, ensure_ascii=False)
    else:
        output_text = result.get("response", "")

    print(output_text)

    # Copy to clipboard if requested
    if copy_clip:
        if copy_to_clipboard(output_text):
            print("\n(Copied to clipboard)", file=sys.stderr)
        else:
            print("\n(Failed to copy to clipboard)", file=sys.stderr)

    # Write to file if requested
    if out_file:
        try:
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"\n(Written to {out_file})", file=sys.stderr)
        except OSError as e:
            print(f"\n(Failed to write to {out_file}: {e})", file=sys.stderr)

    return 0
