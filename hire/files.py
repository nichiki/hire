"""File reference (@filepath) parsing for API-based adapters."""

import os
import re


def extract_file_refs(message: str) -> tuple[str, list[str]]:
    """Extract @filepath references from a message.

    Finds @filepath tokens in the message where the referenced file exists.
    Non-existent paths (e.g., email addresses like aaa@bbb.com) are left as-is.

    Args:
        message: The message potentially containing @filepath references.

    Returns:
        (cleaned_message, file_paths)
        - cleaned_message: Message with resolved @filepath tokens removed.
        - file_paths: List of resolved, existing file paths.
    """
    file_paths: list[str] = []
    # Match @ followed by non-whitespace characters (potential file path)
    # Must be preceded by start-of-string or whitespace
    tokens = re.finditer(r'(?:^|(?<=\s))@(\S+)', message)

    removals: list[tuple[int, int]] = []
    for match in tokens:
        candidate = match.group(1)
        resolved = os.path.abspath(candidate)
        if os.path.exists(resolved):
            file_paths.append(resolved)
            removals.append((match.start(), match.end()))

    if not removals:
        return message, []

    # Build cleaned message by removing matched @filepath tokens
    parts: list[str] = []
    prev = 0
    for start, end in removals:
        parts.append(message[prev:start])
        prev = end
    parts.append(message[prev:])

    cleaned = " ".join(parts).strip()
    # Collapse multiple spaces
    cleaned = re.sub(r' {2,}', ' ', cleaned)

    return cleaned, file_paths
