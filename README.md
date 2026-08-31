<div align="center">

# 🌒 Losna CLI

**An All-Around, Deep AI Terminal Assistant for Code Analysis & Security Auditing**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![OpenRouter BYOK](https://img.shields.io/badge/API-OpenRouter_BYOK-7B2CBF?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-D4AF37?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows_%7C_macOS_%7C_Linux-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#-quick-install)

[Quick Start](#-quick-install) • [Features](#-key-features) • [Commands](#-slash-commands) • [Plugins](#-skill--plugin-system)

</div>

---

> [!NOTE]
> **What makes Losna CLI different?**
> Losna CLI is built for developers, security auditors, and power users who want **raw, deep, untruncated AI responses** directly inside their terminal. Instead of blindly auto-editing your codebase, Losna CLI specializes in **deep code comprehension, architecture inspection, vulnerability detection, and custom skill execution** — giving you 100% control over your API keys (**BYOK**).

---

## Key Features

### Deep Analysis & BYOK (Bring Your Own Key)

- **Bring Your Own Key (BYOK)** — Connect directly to OpenRouter & Tavily. Zero token markup, no middleman limits, and total freedom to choose any model (_DeepSeek V4, Claude 3.5, Gemini 2.5, GPT-4o_).
- **Deep Q&A & Security Auditing** — Built to read large code blocks, analyze architecture, and find security vulnerabilities or logic flaws without truncating long explanations.

### Read-Only Mode (`/readonly`)

- **Strict Safety Toggle** — Lock the agent into Read-Only mode with `/readonly`. Modifying tools (_file writing, editing, replacing, deleting_) and shell command execution are blocked at both schema and runtime levels — safe for auditing production code.
- **Interactive Command Interception** — Destructive shell commands trigger explicit colorized `(y/n)` confirmation before running.

### Web Article Reader & Live Search

- **Article Reader (`read_web_page`)** — Powered by `trafilatura` to extract clean text/markdown from blog posts, documentation, and news URLs.
- **Web Search (`/search`)** — Integrated Tavily web search for real-time documentation, recent news, and online research.

### Performance & UX

- **Multi-Session Chat** — Manage multiple independent chat tabs backed by a local SQLite database (`agent_data.db`).
- **Memory Compaction** — Automatically summarizes older context when history exceeds thresholds to preserve tokens and keep response times fast.
- **Skill & Plugin System** — Add markdown instruction files to `./skills/` or install dynamic prompt plugins directly from GitHub via `/plugin add`.

---

## Quick Install

### Prerequisites

- [Git](https://git-scm.com)
- [Python 3.10+](https://python.org)

### Installation Commands

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/snui1s/losna-cli/main/install.ps1 | iex
```

**macOS / Linux:**

```bash
curl -sSL https://raw.githubusercontent.com/snui1s/losna-cli/main/install.sh | bash
```

After installation, **restart your terminal** and launch:

```bash
losna
```

<details>
<summary><b>What the installer does under the hood</b></summary>

1. Clones this repository into `~/.losna/`
2. Creates an isolated Python virtual environment inside `~/.losna/.venv/`
3. Installs all required dependencies automatically
4. Registers the `losna` command on your system `PATH`

_No global Python packages are modified. Everything is self-contained inside `~/.losna/`._

</details>

<details>
<summary><b>🗑️ Updating & Uninstalling</b></summary>

**Updating:** Re-run the quick install command. The installer detects existing installations and pulls the latest updates.

**Uninstalling (Windows PowerShell):**

```powershell
irm https://raw.githubusercontent.com/snui1s/losna-cli/main/uninstall.ps1 | iex
```

**Uninstalling (macOS / Linux):**

```bash
curl -sSL https://raw.githubusercontent.com/snui1s/losna-cli/main/uninstall.sh | bash
```

</details>

---

## Initial Setup

On first launch, Losna CLI prompts for configuration:

1. **OpenRouter API Key** _(required)_ — Connects to AI models via OpenRouter. Get one at [openrouter.ai](https://openrouter.ai).
2. **Web Search** _(optional)_ — Enable web search using a [Tavily](https://tavily.com) API key.

All keys are stored locally in `~/.losnarc` (JSON format) and are never sent anywhere else.

---

## Slash Commands

| Command                            | Description                                                                   |
| ---------------------------------- | ----------------------------------------------------------------------------- |
| `/help`                            | Show all available commands and loaded skills                                 |
| `/new <title>`                     | Start a new chat session with a custom title                                  |
| `/rename [id] <title>`             | Rename the current or specified chat session                                  |
| `/sessions`                        | List all saved chat sessions with their IDs                                   |
| `/switch <id>`                     | Switch to a different chat session by ID                                      |
| `/delete_session <id>`             | Delete an existing chat session by ID                                         |
| `/history [id]`                    | View chat logs and tool execution history for a session                       |
| `/model`                           | View current OpenRouter model or switch to a new model ID                     |
| `/readonly`                        | Toggle Read-Only Mode (blocks file modification & shell execution)            |
| `/diff [file\|session]`            | View colored syntax-highlighted git diff for a file or session memory state   |
| `/enter2confirm`                   | Toggle double-Enter requirement before sending prompts to AI                  |
| `/pin <text>`                      | Pin a custom rule/fact to AI Core Memory (remembered forever across sessions) |
| `/pins`                            | List all pinned Core Memory rules with their database IDs                     |
| `/unpin <id>`                      | Unpin/remove a Core Memory rule by ID or exact text                           |
| `/export [path]`                   | Export active session chat log into a structured Markdown document            |
| `/clear`                           | Clear terminal screen and re-render header banner                             |
| `/ls [path]`                       | List directory files and folders in clean formatted view                      |
| `/cd <path>`                       | Change working directory (supports '..', '~', and '-')                        |
| `/init-ai`                         | Generate a starter 'ai.txt' blueprint file for project auto-detection         |
| `/max_tool_calls [n]`              | View or set maximum tool call limit per turn (persisted in ~/.losnarc)        |
| `/plugin add <url>`                | Download and install all skills from a GitHub repository                      |
| `/plugin add <url> --skill <name>` | Download and install a specific skill from a GitHub repository                |
| `/plugin remove <name>`            | Uninstall/remove a custom skill plugin from local project                     |
| `/plugin list`                     | List all installed skill plugins and their enabled status                     |
| `/plugin enable <name>`            | Enable a disabled skill plugin globally                                       |
| `/plugin disable <name>`           | Disable an active skill plugin globally                                       |
| `/<skill> off\|on\|status`         | Quick toggle or status check for an individual skill                          |
| `/search <query>`                  | Search the web using Tavily and synthesize results                            |
| `/usage`                           | Show session token usage and estimated cost breakdown                         |
| `/exit` or `/quit`                 | Exit Losna CLI session                                                        |

### 💡 Slash Command Examples

```bash
# File Context & Workspace Inspection
/init-ai
@src/agent/main.py Summarize this file
/ls
/ls src/agent
/cd src/agent
/cd ..
/cd -

# Plugin & Skill Management
/plugin add https://github.com/JuliusBrussee/caveman
/plugin disable caveman
/plugin enable caveman
/plugin list
/caveman off
/caveman on

# Core Memory & Rule Pinning
/pin Always write type hints and docstrings for functions
/pins
/unpin 1

# Tool Execution & Session Controls
/max_tool_calls 50
/diff src/agent/main.py
/export ./exports/session_notes.md
/switch 3
```

---

## Skill & Plugin System

Project skills stored in `./skills/<skill-name>/SKILL.md` are automatically recognized as slash commands (e.g., `/unit-testing`).

### Installing Plugins from GitHub

```bash
# Install all skills from a repository
/plugin add https://github.com/JuliusBrussee/caveman

# Install a specific skill from a repository
/plugin add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices
```

### Removing Plugins

```bash
# Interactive selection list
/plugin remove

# Direct removal by name
/plugin remove caveman
```

### Writing Custom Skills

Create `./skills/my-custom-skill/SKILL.md` in your project:

```markdown
---
name: my-custom-skill
description: Custom team coding guidelines and security review rules.
---

# Instructions

1. Always check for memory leaks and unchecked input...
2. Use strict typing...
```

---

## Project Structure

```
losna-cli/
├── src/
│   └── agent/
│       ├── main.py          # Application entry point
│       ├── config.py        # Configuration and API key management
│       ├── db.py            # SQLite persistence layer
│       ├── tools.py         # Agent tool definitions, web reader & dispatcher
│       ├── prompts.py       # System prompt builder & Read-Only constraints
│       ├── session.py       # Session selection & management
│       ├── memory.py        # Memory compaction logic
│       ├── skills_loader.py # Dynamic skill loading from project files
│       ├── plugin_manager.py# Remote plugin package installer
│       └── ui.py            # Terminal UI (spinners, banners, markdown renderer)
├── evals/                   # LLM evaluation datasets, metrics & benchmark runner
├── skills/                  # Local project skill definitions
├── tests/                   # Automated pytest suite
├── install.ps1              # Windows installer
├── install.sh               # macOS/Linux installer
├── pyproject.toml           # Package metadata, dependencies & bump-my-version
└── README.md
```

---

## LLM Evals & Benchmarking

Losna CLI includes a dedicated LLM evaluation and benchmarking suite using **DeepEval** to test prompt performance, tool dispatch accuracy, memory compaction, and security audit quality.

### Running Evals & Benchmarks

```bash
# Run deterministic unit evaluations via pytest
pytest evals/ -v

# Run benchmark runner in dry-run mode (offline)
python -m evals.run_benchmarks --dry-run

# Run live benchmark against target OpenRouter model and export scorecard
python -m evals.run_benchmarks --model anthropic/claude-3.5-sonnet --output benchmark_scorecard.md
```
