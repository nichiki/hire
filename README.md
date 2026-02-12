# hire-ai

CLI to orchestrate AI agents (Claude, Codex, Gemini, Grok).

> **⚠️ Warning**: By default, CLI agents run in **auto-approve mode**:
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

# Using Homebrew (macOS)
brew install nichiki/tap/hire-ai
```

## Prerequisites

You need at least one of the following:

- [Claude Code](https://claude.ai/claude-code) (CLI)
- [Codex](https://github.com/openai/codex) (CLI)
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) (CLI)
- [Grok](https://console.x.ai/) (API key only, no CLI needed)

## Usage

```bash
# Basic usage - hire an agent
hire codex "Design a REST API for a todo app"
hire gemini "Research the latest React 19 features"
hire claude "Review this code for security issues"
hire grok "Analyze this codebase"

# Continue a session
hire -c codex "Tell me more about the authentication"
hire -s SESSION_ID "Follow up question"

# Name a session for later
hire -n my-project codex "Start designing the architecture"
hire -s my-project "What about the database schema?"

# Pipe input
cat main.py | hire codex "Review this code"
git diff | hire claude "Explain these changes"
echo "What is 2+2?" | hire gemini

# Attach files (using @filepath)
hire claude "Review @src/main.py for security issues"
hire codex "Explain @package.json and @tsconfig.json"
hire grok "Summarize @report.pdf"

# Output as JSON
hire gemini "Summarize this" --json

# Copy to clipboard
hire codex "Write a function" --clip

# Write to file
hire claude "Generate a README" -o README.md

# Session management
hire sessions              # List all sessions
hire sessions codex        # List sessions by agent
hire show SESSION_ID       # Show session details
hire delete SESSION_ID     # Delete a session
hire delete --all          # Delete all sessions

# Check environment
hire doctor                # Check installed agents and config
```

## Options

| Option | Description |
|--------|-------------|
| `-c, --continue` | Continue the latest session |
| `-s, --session ID` | Continue a specific session |
| `-n, --name NAME` | Name the session |
| `-m, --model MODEL` | Specify model to use |
| `--json` | Output in JSON format |
| `--clip` | Copy output to clipboard |
| `-o, --out FILE` | Write output to file |

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
    },
    "grok": {
      "model": "grok-4-latest",
      "api_key": "xai-..."
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
