"""Codex CLI adapter."""

import json
import shutil
import subprocess
from typing import Any

from ..config import get_adapter_config
from .base import AgentAdapter


class CodexAdapter(AgentAdapter):
    """Adapter for Codex CLI."""

    name = "codex"

    def build_command(
        self,
        message: str,
        session_id: str | None = None,
        model: str | None = None,
    ) -> list[str]:
        """Build the codex command."""
        config = get_adapter_config("codex")
        command = config.get("command", "codex")
        # Resolve full path for Windows .cmd/.bat files
        resolved = shutil.which(command)
        if resolved:
            command = resolved
        args = config.get("args", [])

        if session_id:
            # Resume session: codex exec resume <SESSION_ID> "message"
            cmd = [command, "exec", "resume", session_id, message, "--json", "--skip-git-repo-check"]
        else:
            # New session: codex exec "message"
            cmd = [command, "exec", message, "--json", "--skip-git-repo-check"]

        cmd.extend(args)

        if model:
            cmd.extend(["--model", model])

        return cmd

    def ask(
        self,
        message: str,
        session_id: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Send a message to Codex and get a response."""
        cmd = self.build_command(message, session_id, model)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if result.returncode != 0:
            return {
                "response": None,
                "session_id": session_id,
                "error": result.stderr or "Command failed",
                "raw": result.stdout,
            }

        # Codex outputs JSONL (one JSON object per line)
        # Parse all lines and extract the final response
        lines = result.stdout.strip().split("\n")
        response_text = ""
        new_session_id = session_id

        for line in lines:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                event_type = event.get("type", "")

                # Get thread_id from thread.started event
                if event_type == "thread.started":
                    new_session_id = event.get("thread_id", new_session_id)

                # Get response text from item.completed with agent_message
                if event_type == "item.completed":
                    item = event.get("item", {})
                    if item.get("type") == "agent_message":
                        response_text = item.get("text", "")

            except json.JSONDecodeError:
                continue

        # If no structured response found, use raw output
        if not response_text:
            response_text = result.stdout.strip()

        return {
            "response": response_text,
            "session_id": new_session_id,
            "raw": result.stdout,
        }
