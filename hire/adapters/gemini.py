"""Gemini CLI adapter."""

import json
import shutil
import subprocess
from typing import Any

from ..config import get_adapter_config
from .base import AgentAdapter


class GeminiAdapter(AgentAdapter):
    """Adapter for Gemini CLI."""

    name = "gemini"

    def build_command(
        self,
        message: str,
        session_id: str | None = None,
        model: str | None = None,
    ) -> list[str]:
        """Build the gemini command."""
        config = get_adapter_config("gemini")
        command = config.get("command", "gemini")
        # Resolve full path for Windows .cmd/.bat files
        resolved = shutil.which(command)
        if resolved:
            command = resolved
        args = config.get("args", [])

        # gemini -p "message" -o json -y
        cmd = [command, "-p", message, "-o", "json"]
        cmd.extend(args)

        # Resume uses "latest" or index number, not session ID
        if session_id:
            cmd.extend(["-r", session_id])

        if model:
            cmd.extend(["-m", model])

        return cmd

    def ask(
        self,
        message: str,
        session_id: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Send a message to Gemini and get a response."""
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

        # Try to parse JSON output
        try:
            data = json.loads(result.stdout)
            # Extract response - structure may vary
            response_text = ""
            new_session_id = session_id

            if isinstance(data, dict):
                response_text = data.get("result", data.get("response", data.get("text", "")))
                new_session_id = data.get("session_id", data.get("sessionId", session_id))
            elif isinstance(data, str):
                response_text = data

            # For continuation, use "latest" as session identifier
            if not new_session_id:
                new_session_id = "latest"

            return {
                "response": response_text,
                "session_id": new_session_id,
                "raw": data,
            }
        except json.JSONDecodeError:
            # Plain text output
            return {
                "response": result.stdout.strip(),
                "session_id": "latest",  # Use "latest" for continuation
                "raw": result.stdout,
            }
