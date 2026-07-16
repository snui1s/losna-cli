# Losna CLI

A terminal-based AI developer assistant powered by OpenRouter. Losna CLI brings an intelligent coding companion directly into your terminal with multi-session chat management, tool execution, web search, and persistent memory.

## Features

### Core

- **Interactive AI Shell** — Full conversational interface powered by OpenRouter models (defaults to Deepseek V4 Flash). Includes slash command autocompletion, input history suggestions, and styled markdown output with gold-themed headers.
- **Multi-Session Chat** — Create, switch between, and manage multiple independent chat sessions. Each session maintains its own conversation history stored in a local SQLite database.
- **Tool Execution** — The AI agent can execute shell commands, read and write files, run tests, and perform file system operations on your behalf within the current working directory.

### Intelligence

- **Memory Compaction** — Automatically compresses older conversation context when the message history exceeds configurable thresholds, preserving a summary of previous discussions while keeping token costs low.
- **Skill System** — Drop markdown instruction files into a `skills/` directory in your project. The agent can dynamically load and follow these instructions via slash commands (e.g., `/unit-testing`).
- **Web Search** — Optional, agent-driven web search powered by Tavily. The `/search` command instructs the AI to query the web and synthesize results. Tavily API key is only requested when you first use this feature.

### User Experience

- **Styled Terminal Output** — Agent responses are rendered as rich markdown with gold-themed headers, styled blockquotes, and syntax-highlighted code blocks.
- **Live Typewriter Effect** — Responses appear progressively with a typewriter animation for a natural conversational feel.
- **Dynamic Spinners** — Moon-phase animated spinners display during AI processing and tool execution, with success checkmarks on completion.

## Installation

### Prerequisites

- [Git](https://git-scm.com)
- [Python 3.10+](https://python.org)

### Quick Install

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/snui1s/losna-cli/main/install.ps1 | iex
```

**macOS / Linux:**

```bash
curl -sSL https://raw.githubusercontent.com/snui1s/losna-cli/main/install.sh | bash
```

After installation, **restart your terminal** and run:

```
losna
```

### What the installer does

1. Clones this repository to `~/.losna/`
2. Creates an isolated Python virtual environment inside `~/.losna/.venv/`
3. Installs all required dependencies automatically
4. Registers the `losna` command on your system PATH

No global Python packages are modified. Everything is self-contained inside `~/.losna/`.

### Updating

Run the same install command again. The installer detects the existing installation, pulls the latest changes from GitHub, and updates dependencies automatically.

### Uninstalling

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/snui1s/losna-cli/main/uninstall.ps1 | iex
```

**macOS / Linux:**

```bash
curl -sSL https://raw.githubusercontent.com/snui1s/losna-cli/main/uninstall.sh | bash
```

**Manual removal:**

```powershell
# Windows
Remove-Item -Recurse -Force "$env:USERPROFILE\.losna"

# macOS / Linux
rm -rf ~/.losna ~/.local/bin/losna
```

## Setup

On first launch, Losna CLI will guide you through the initial configuration:

1. **OpenRouter API Key** (required) — Used to communicate with the AI model. Get one at [openrouter.ai](https://openrouter.ai).
2. **Web Search** (optional) — You will be asked whether you want to enable web search. If yes, you will be prompted for a [Tavily](https://tavily.com) API key.

All keys are stored locally in `~/.losnarc` (JSON format). They are never transmitted anywhere other than their respective API endpoints.

## Usage

Navigate to any project directory and launch the assistant:

```bash
cd ~/my-project
losna
```

The agent operates in the context of your current working directory. It can read your project files, execute commands, and create or modify files within that directory.

### Commands

| Command | Description |
|---|---|
| `/help` | Show all available commands and loaded skills |
| `/new <title>` | Start a new chat session with a custom title |
| `/sessions` | List all saved chat sessions with their IDs |
| `/switch <id>` | Switch to a different chat session by ID |
| `/search <query>` | Instruct the agent to search the web and report findings |
| `/exit` or `/quit` | Close the current session |

### Skill Commands

If your project contains a `skills/` directory with markdown instruction files, they will appear as additional slash commands. For example, a file at `skills/unit-testing/SKILL.md` becomes available as `/unit-testing`.

## Project Structure

```
losna-cli/
  src/
    agent/
      main.py          # Application entry point
      config.py         # Configuration and API key management
      db.py             # SQLite persistence layer
      tools.py          # Agent tool definitions and dispatch
      prompts.py        # System prompt builder
      session.py        # Session selection and management
      memory.py         # Memory compaction logic
      skills_loader.py  # Dynamic skill loading from project files
      ui.py             # Terminal UI (spinner, banner, markdown renderer)
  skills/               # Project-level skill definitions (optional)
  install.ps1           # Windows installer
  install.sh            # macOS/Linux installer
  uninstall.ps1         # Windows uninstaller
  pyproject.toml        # Package metadata and dependencies
```
