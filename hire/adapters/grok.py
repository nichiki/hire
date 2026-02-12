"""Grok API adapter (direct xAI API call, no CLI dependency)."""

import json
import os
import sys
import urllib.request
import urllib.error
from typing import Any

from ..config import get_adapter_config
from .base import AgentAdapter

DEFAULT_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4-latest"


def _get_api_key() -> str | None:
    """Get Grok API key from hire config or environment variable."""
    config = get_adapter_config("grok")
    key = config.get("api_key")
    if key:
        return key

    return os.environ.get("GROK_API_KEY")


def _upload_file(api_key: str, file_path: str, base_url: str) -> str:
    """Upload a file to xAI Files API.

    Returns:
        The file ID for use in Responses API.
    """
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_data = f.read()

    # Build multipart/form-data manually (no external deps)
    boundary = f"----hire-ai-{os.urandom(16).hex()}"

    body = b""
    # File field
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    body += file_data
    body += b"\r\n"
    # Purpose field
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="purpose"\r\n\r\n'
    body += b"assistants\r\n"
    # End
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{base_url}/files",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "hire-ai",
        },
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    return data["id"]


class GrokAdapter(AgentAdapter):
    """Adapter for Grok via xAI Responses API with web/X search."""

    name = "grok"

    def ask(
        self,
        message: str,
        session_id: str | None = None,
        model: str | None = None,
        history: list[dict[str, str]] | None = None,
        files: list[str] | None = None,
    ) -> dict[str, Any]:
        """Send a message to Grok via xAI Responses API."""
        api_key = _get_api_key()
        if not api_key:
            return {
                "response": None,
                "session_id": None,
                "error": "Grok API key not found. Set api_key in config or GROK_API_KEY env var",
                "raw": "",
            }

        config = get_adapter_config("grok")
        base_url = config.get("base_url", DEFAULT_BASE_URL)
        model = model or config.get("model", DEFAULT_MODEL)

        # Upload files if provided
        file_ids: list[str] = []
        if files:
            for file_path in files:
                try:
                    print(f"Uploading {os.path.basename(file_path)}...", file=sys.stderr)
                    file_id = _upload_file(api_key, file_path, base_url)
                    file_ids.append(file_id)
                except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
                    return {
                        "response": None,
                        "session_id": None,
                        "error": f"File upload failed for {file_path}: {e}",
                        "raw": "",
                    }

        # Build input: history + new message
        messages = list(history) if history else []

        if file_ids:
            # Use structured content array with file references
            content: list[dict[str, str]] = [{"type": "input_text", "text": message}]
            for fid in file_ids:
                content.append({"type": "input_file", "file_id": fid})
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": message})

        payload = {
            "model": model,
            "input": messages,
            "tools": [
                {"type": "web_search"},
                {"type": "x_search"},
            ],
        }

        req = urllib.request.Request(
            f"{base_url}/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "hire-ai",
            },
        )

        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # Responses API: extract text from output items
            response_text = ""
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for part in item.get("content", []):
                        if part.get("type") == "output_text":
                            response_text += part.get("text", "")

            if not response_text:
                response_text = json.dumps(data, ensure_ascii=False)

            return {
                "response": response_text,
                "session_id": None,
                "raw": data,
            }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            return {
                "response": None,
                "session_id": None,
                "error": f"Grok API error: {e.code} {error_body}",
                "raw": error_body,
            }
        except urllib.error.URLError as e:
            return {
                "response": None,
                "session_id": None,
                "error": f"Connection error: {e.reason}",
                "raw": "",
            }
