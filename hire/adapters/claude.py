"""Claude CLI adapter."""

import json
import shutil
import subprocess
from typing import Any

from ..config import get_adapter_config
from .base import AgentAdapter


class ClaudeAdapter(AgentAdapter):
    """Adapter for Claude CLI."""

    name = "claude"

    def build_command(
        self,
        message: str,
        session_id: str | None = None,
        model: str | None = None,
    ) -> list[str]:
        """Build the claude command."""
        config = get_adapter_config("claude")
        command = config.get("command", "claude")
        # Resolve full path for Windows .cmd/.bat files
        resolved = shutil.which(command)
        if resolved:
            command = resolved
        args = config.get("args", [])

        cmd = [command, "-p", message, "--output-format", "json"]
        cmd.extend(args)

        if session_id:
            cmd.extend(["--resume", session_id])

        if model:
            cmd.extend(["--model", model])

        return cmd

    def ask(
        self,
        message: str,
        session_id: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Send a message to Claude and get a response."""
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

        try:
            data = json.loads(result.stdout)
            return {
                "response": data.get("result", ""),
                "session_id": data.get("session_id", session_id),
                "raw": data,
            }
        except json.JSONDecodeError:
            # If not JSON, return raw output
            return {
                "response": result.stdout,
                "session_id": session_id,
                "raw": result.stdout,
            }
