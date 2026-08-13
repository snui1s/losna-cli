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

## ✨ Key Features

### 🧠 Deep Analysis & BYOK (Bring Your Own Key)
- **Bring Your Own Key (BYOK)** — Connect directly to OpenRouter & Tavily. Zero token markup, no middleman limits, and total freedom to choose any model (*DeepSeek V4, Claude 3.5, Gemini 2.5, GPT-4o*).
- **Deep Q&A & Security Auditing** — Built to read large code blocks, analyze architecture, and find security vulnerabilities or logic flaws without truncating long explanations.

### 🛡️ Read-Only Mode (`/readonly`)
- **Strict Safety Toggle** — Lock the agent into Read-Only mode with `/readonly`. Modifying tools (*file writing, editing, replacing, deleting*) and shell command execution are blocked at both schema and runtime levels — safe for auditing production code.
- **Interactive Command Interception** — Destructive shell commands trigger explicit colorized `(y/n)` confirmation before running.

### 🔍 Web Article Reader & Live Search
- **Article Reader (`read_web_page`)** — Powered by `trafilatura` to extract clean text/markdown from blog posts, documentation, and news URLs.
- **Web Search (`/search`)** — Integrated Tavily web search for real-time documentation, recent news, and online research.

### ⚡ Performance & UX
- **Multi-Session Chat** — Manage multiple independent chat tabs backed by a local SQLite database (`agent_data.db`).
- **Memory Compaction** — Automatically summarizes older context when history exceeds thresholds to preserve tokens and keep response times fast.
- **Skill & Plugin System** — Add markdown instruction files to `./skills/` or install dynamic prompt plugins directly from GitHub via `/plugin add`.

---

## ⚡ Quick Install

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
<summary><b>🔍 What the installer does under the hood</b></summary>

1. Clones this repository into `~/.losna/`
2. Creates an isolated Python virtual environment inside `~/.losna/.venv/`
3. Installs all required dependencies automatically
4. Registers the `losna` command on your system `PATH`

*No global Python packages are modified. Everything is self-contained inside `~/.losna/`.*
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

## 🔑 Initial Setup

On first launch, Losna CLI prompts for configuration:

1. **OpenRouter API Key** *(required)* — Connects to AI models via OpenRouter. Get one at [openrouter.ai](https://openrouter.ai).
2. **Web Search** *(optional)* — Enable web search using a [Tavily](https://tavily.com) API key.

All keys are stored locally in `~/.losnarc` (JSON format) and are never sent anywhere else.

---

## 💻 Slash Commands

| Command | Description |
|---|---|
| `/help` | Show all available commands and loaded skills |
| `/new <title>` | Start a new chat session with a custom title |
| `/sessions` | List all saved chat sessions with their IDs |
| `/switch <id>` | Switch to a different chat session by ID |
| `/delete_session <id>` | Delete an existing chat session by ID |
| `/history [id]` | View chat logs and tool execution history for a session |
| `/model` | View current OpenRouter model or switch to a new model ID |
| `/readonly` | Toggle Read-Only Mode (blocks file modification & shell execution) |
| `/plugin add <url>` | Download and install all skills from a GitHub repository |
| `/plugin add <url> --skill <name>` | Download and install a specific skill from a GitHub repository |
| `/plugin remove` | Show interactive list of installed plugins to choose for removal |
| `/plugin remove <name>` | Uninstall/remove a specific skill plugin from local project |
| `/search <query>` | Search the web using Tavily and synthesize results |
| `/exit` or `/quit` | Exit Losna CLI session |

---

## 🔌 Skill & Plugin System

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

## 📂 Project Structure

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
├── skills/                  # Local project skill definitions
├── tests/                   # Automated pytest suite
├── install.ps1              # Windows installer
├── install.sh               # macOS/Linux installer
├── pyproject.toml           # Package metadata, dependencies & bump-my-version
└── README.md
```