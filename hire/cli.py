"""CLI entry point."""

import argparse
import sys

from . import __version__
from .commands import run_ask, run_delete, run_doctor, run_sessions, run_show


SUBCOMMANDS = {"sessions", "show", "delete", "doctor", "help", "--help", "-h", "--version"}


def main() -> int:
    """Main entry point."""
    # Ensure UTF-8 output on Windows
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    # Check if first arg is a subcommand, if not, treat as default (hire) action
    if len(sys.argv) > 1 and sys.argv[1] not in SUBCOMMANDS:
        # Default action: hire an agent
        return run_default()

    # Subcommand mode
    parser = argparse.ArgumentParser(
        prog="hire",
        description="Hire AI agents to do tasks (Claude, Codex, Gemini, Grok)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # sessions command
    sessions_parser = subparsers.add_parser("sessions", help="List sessions")
    sessions_parser.add_argument(
        "target",
        nargs="?",
        choices=["claude", "codex", "gemini", "grok"],
        help="Filter by agent",
    )
    sessions_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )

    # show command
    show_parser = subparsers.add_parser("show", help="Show session details")
    show_parser.add_argument(
        "name_or_id",
        help="Session name or ID",
    )
    show_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a session")
    delete_parser.add_argument(
        "name_or_id",
        nargs="?",
        help="Session name or ID",
    )
    delete_parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Delete all sessions",
    )
    delete_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Delete without confirmation",
    )

    # doctor command
    subparsers.add_parser("doctor", help="Check environment and agent availability")

    args = parser.parse_args()

    if args.command is None:
        print_usage()
        return 0

    # Dispatch to command handlers
    if args.command == "sessions":
        return run_sessions(args)
    elif args.command == "show":
        return run_show(args)
    elif args.command == "delete":
        return run_delete(args)
    elif args.command == "doctor":
        return run_doctor(args)
    else:
        print_usage()
        return 1


def run_default() -> int:
    """Run the default hire action."""
    parser = argparse.ArgumentParser(
        prog="hire",
        description="Hire AI agents to do tasks",
        usage="hire [options] <target> <message>\n       hire <subcommand> [args]",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Target agent: claude, codex, gemini, or grok",
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Message to send",
    )
    parser.add_argument(
        "-c", "--continue",
        dest="continue_session",
        action="store_true",
        help="Continue the latest session",
    )
    parser.add_argument(
        "-s", "--session",
        help="Continue a specific session (by name or ID)",
    )
    parser.add_argument(
        "-n", "--name",
        help="Name for the session",
    )
    parser.add_argument(
        "-m", "--model",
        help="Model to use",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    parser.add_argument(
        "--clip",
        action="store_true",
        help="Copy output to clipboard",
    )
    parser.add_argument(
        "-o", "--out",
        metavar="FILE",
        help="Write output to file",
    )

    args = parser.parse_args()
    return run_ask(args)


def print_usage():
    """Print usage information."""
    print("""hire - Hire AI agents to do tasks (Claude, Codex, Gemini, Grok)

Usage:
  hire <target> <message>      Hire an agent to do a task
  hire -s <session> <message>  Continue a specific session
  hire sessions [target]       List sessions
  hire show <name-or-id>       Show session details
  hire delete <name-or-id>     Delete a session
  hire delete --all            Delete all sessions
  hire doctor                  Check environment

Targets:
  claude, codex, gemini, grok

Options:
  -c, --continue     Continue the latest session
  -s, --session ID   Continue a specific session
  -n, --name NAME    Name the session
  -m, --model MODEL  Specify model
  --json             Output in JSON format
  --clip             Copy output to clipboard
  -o, --out FILE     Write output to file

Examples:
  hire codex "Design a REST API"
  hire gemini "Research React 19 features" --json
  hire -s abc123 "Tell me more"
  hire sessions codex
""")


if __name__ == "__main__":
    sys.exit(main())
