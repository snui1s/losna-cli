# Losna CLI

A terminal-based AI developer assistant powered by OpenRouter. Losna CLI brings an intelligent coding companion directly into your terminal with multi-session chat management, tool execution, web search, and persistent memory.

## Features

### Core

- **Interactive AI Shell** — Full conversational interface powered by OpenRouter models (defaults to Deepseek V4 Flash). Includes slash command autocompletion, input history suggestions, and styled markdown output with gold-themed headers.
- **Multi-Session Chat** — Create, switch between, and manage multiple independent chat sessions. Each session maintains its own conversation history stored in a local SQLite database.
- **Tool Execution** — The AI agent can execute shell commands, read and write files, run tests, and perform file system operations on your behalf within the current working directory.

### Intelligence

- **Memory Compaction** — Automatically compresses older conversation context when the message history exceeds configurable thresholds, preserving a summary of previous discussions while keeping token costs low.
- **Skill & Plugin System** — Add markdown instruction files to `./skills/` or install plugins directly from remote repositories via `/plugin`. The agent dynamically loads and follows these instructions.
- **Web Search** — Optional, agent-driven web search powered by Tavily. The `/search` command instructs the AI to query the web and synthesize results. Tavily API key is only requested when you first use this feature.

### User Experience

- **Styled Terminal Output** — Agent responses are rendered as rich markdown with gold-themed headers, styled blockquotes, and syntax-highlighted code blocks.
- **Interactive Command Confirmation** — The CLI intercepts dangerous system commands or file deletions, stops the active spinner, and requests confirmation in colorized (`y`/`n`) text to ensure safety.
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
| `/delete_session <id>` | Delete an existing chat session by its ID |
| `/history [id]` | View chat logs and tool execution history for a session (defaults to current) |
| `/model` | View the current OpenRouter model or switch to a new model ID |
| `/plugin add <url>` | Download and install all skills in a GitHub repository |
| `/plugin add <url> --skill <name>` | Download and install one specific skill from a GitHub repository |
| `/plugin remove` | Show a numbered list of installed plugins to choose for removal |
| `/plugin remove <name>` | Uninstall/remove a specific custom skill plugin from project |
| `/search <query>` | Instruct the agent to search the web and report findings |
| `/exit` or `/quit` | Close the current session |

### Skill & Plugin Commands

If your project contains a `skills/` directory with markdown instruction files, they will appear as additional slash commands. For example, a file at `skills/unit-testing/SKILL.md` becomes available as `/unit-testing`.

#### Installing Plugins from GitHub

You can dynamically import custom skills and prompt packages directly into your project's local workspace from remote Git repositories using the `/plugin` command:

**Option A: Install all skills from a repository (Auto-detect)**
If you do not specify a skill name, Losna CLI scans the repository and installs every skill it finds:
```bash
/plugin add https://github.com/JuliusBrussee/caveman
```

**Option B: Install only one specific skill**
Use the `--skill` option followed by the folder name to install only a single skill:
```bash
/plugin add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices
```

#### Uninstalling/Removing a plugin

**Option A: Interactive List Selection (Recommended)**
Type the command without arguments. Losna CLI will show a numbered list of installed skills for you to pick and delete:
```bash
/plugin remove
```

**Option B: Delete directly by name**
If you already know the name of the skill/plugin folder, you can delete it immediately:
```bash
/plugin remove caveman
```

#### Writing Custom Plugins

A Losna CLI plugin is simple. To write your own, create the following directory structure in your project:

```
skills/
  my-custom-skill/
    SKILL.md
```

Inside `SKILL.md`, define a YAML header at the top, followed by markdown instructions for the AI:

```markdown
---
name: my-custom-skill
description: Guides the agent on how to write code according to my team's style guide.
---
# Instructions
When this skill is invoked:
1. Always prefix variable names with...
2. Use strict typing...
```

Once saved, the command `/my-custom-skill` becomes instantly available via autocomplete in the Losna prompt. Calling `/my-custom-skill <your request>` will prompt the agent to read and follow these rules.

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
      plugin_manager.py # Remote plugin cloning and package installer
      ui.py             # Terminal UI (spinner, banner, markdown renderer)
  skills/               # Project-level skill definitions (optional)
  install.ps1           # Windows installer
  install.sh            # macOS/Linux installer
  uninstall.ps1         # Windows uninstaller
  uninstall.sh          # macOS/Linux uninstaller
  pyproject.toml        # Package metadata and dependencies
```

## License

Apache License 2.0
