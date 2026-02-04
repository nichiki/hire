# hire-ai

CLI to orchestrate AI agents (Claude, Codex, Gemini).

> **⚠️ Warning**: By default, all agents run in **auto-approve mode**:
> - Claude Code: `--dangerously-skip-permissions`
> - Codex: `--full-auto`
> - Gemini CLI: `-y`
>
> This means agents can execute commands and modify files without confirmation.
> You can customize this in `~/.config/hire/config.json`.

## Installation

```bash
# Using pipx (recommended)
pipx install hire-ai

# Using pip
pip install hire-ai

# Using Homebrew (coming soon)
# brew install nichiki/tap/hire
```

## Prerequisites

You need at least one of the following CLI tools installed:

- [Claude Code](https://claude.ai/claude-code)
- [Codex](https://github.com/openai/codex)
- [Gemini CLI](https://github.com/google-gemini/gemini-cli)

## Usage

```bash
# Basic usage - hire an agent
hire codex "Design a REST API for a todo app"
hire gemini "Research the latest React 19 features"
hire claude "Review this code for security issues"

# Continue a session
hire -c codex "Tell me more about the authentication"
hire -s SESSION_ID "Follow up question"

# Name a session for later
hire -n my-project codex "Start designing the architecture"
hire -s my-project "What about the database schema?"

# Output as JSON
hire gemini "Summarize this" --json

# Session management
hire sessions              # List all sessions
hire sessions codex        # List Codex sessions only
hire show SESSION_ID       # Show session details
hire delete SESSION_ID     # Delete a session
```

## Options

| Option | Description |
|--------|-------------|
| `-c, --continue` | Continue the latest session |
| `-s, --session ID` | Continue a specific session |
| `-n, --name NAME` | Name the session |
| `-m, --model MODEL` | Specify model to use |
| `--json` | Output in JSON format |

## Configuration

Config is stored at `~/.config/hire/config.json`:

```json
{
  "adapters": {
    "claude": {
      "command": "claude",
      "args": ["--dangerously-skip-permissions"]
    },
    "codex": {
      "command": "codex",
      "args": ["--full-auto"]
    },
    "gemini": {
      "command": "gemini",
      "args": ["-y"]
    }
  },
  "defaults": {
    "agent": "claude"
  }
}
```

## Data Storage

Sessions are stored at `~/.local/share/hire/sessions/`.

## License

MIT
