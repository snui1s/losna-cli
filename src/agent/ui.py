"""
ui.py — Terminal User Interface (TUI) and output rendering module.

Provides prompt_toolkit session wrappers with autocomplete, Rich-based markdown
response rendering, ASCII banner display, and non-blocking background update checks.
"""

import threading
import sys
import time
import os
import json
import re

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from . import config


class PromptCompleter(Completer):
    """
    Suggests completions for slash commands ('/') and workspace file mentions ('@').
    """

    def __init__(self, commands):
        """
        Initializes PromptCompleter with slash command list.

        Args:
            commands (list[str]): List of valid slash commands.
        """
        self.commands = sorted(commands)

    def get_completions(self, document, complete_event):
        """
        Yields autocompletion suggestions based on current cursor document text.

        Args:
            document: Prompt_toolkit Document object.
            complete_event: Prompt_toolkit CompleteEvent object.
        """
        text_before = document.text_before_cursor
        word_before = document.get_word_before_cursor(WORD=True)

        # 1. Slash commands completion at start of input line
        if text_before.lstrip().startswith('/') and ' ' not in text_before.lstrip():
            text_lower = text_before.lstrip().lower()
            for cmd in self.commands:
                if cmd.lower().startswith(text_lower):
                    yield Completion(cmd, start_position=-len(text_before.lstrip()))
            return

        # 2. File mention completion when typing '@'
        if '@' in word_before:
            at_idx = word_before.rfind('@')
            mention_prefix = word_before[at_idx + 1:]

            try:
                base_dir = os.getcwd()
                rel_prefix = mention_prefix.replace("\\", "/")
                # Directories to skip during file mention autocomplete
                _SKIP_DIRS = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', '.mypy_cache', '.pytest_cache', 'dist', 'build', '.tox', '.eggs'}

                count = 0
                for root, dirs, files in os.walk(base_dir):
                    dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith('.')]
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), base_dir).replace("\\", "/")
                        if rel_path.lower().startswith(rel_prefix.lower()):
                            yield Completion(f"@{rel_path}", start_position=-len(word_before[at_idx:]))
                            count += 1
                            if count >= 30:  # Limit suggestions
                                break
                    if count >= 30 or root.count(os.sep) - base_dir.count(os.sep) >= 2:
                        dirs.clear()
            except Exception:
                pass
            return

        # 3. Dynamic directory autocompletion when typing '/cd ' or '/ls '
        clean_text = text_before.lstrip()
        if clean_text.startswith(('/cd ', '/ls ')):
            parts = clean_text.split(maxsplit=1)
            path_part = parts[1] if len(parts) > 1 else ""

            if not path_part:
                target_dir = os.getcwd()
                search_prefix = ""
                replace_len = 0
            else:
                raw_path = path_part.replace("\\", "/")
                if raw_path.endswith("/"):
                    target_dir = os.path.abspath(raw_path)
                    search_prefix = ""
                    replace_len = 0
                else:
                    target_dir = os.path.dirname(os.path.abspath(raw_path))
                    search_prefix = os.path.basename(raw_path)
                    replace_len = len(search_prefix)

            try:
                if os.path.exists(target_dir) and os.path.isdir(target_dir):
                    candidates = []
                    if "..".startswith(search_prefix.lower()):
                        candidates.append("..")

                    for item in sorted(os.listdir(target_dir)):
                        if item.startswith(".") and not search_prefix.startswith(".") and item not in [".env", ".losnarc"]:
                            continue
                        full_item = os.path.join(target_dir, item)
                        if os.path.isdir(full_item):
                            if item.lower().startswith(search_prefix.lower()):
                                candidates.append(item)

                    for cand in candidates:
                        display_str = f"📁 {cand}/" if cand != ".." else "📁 ../"
                        completion_val = f"{cand}/" if cand != ".." else "../"
                        yield Completion(
                            completion_val,
                            start_position=-replace_len,
                            display=display_str
                        )
            except Exception:
                pass


# Backward-compatibility alias
SlashCompleter = PromptCompleter


class Spinner:
    """
    Threaded terminal progress spinner with rotating moon phase indicators.
    """

    def __init__(self, message="Loading"):
        """
        Initializes the spinner instance.

        Args:
            message (str, optional): Loading text label. Defaults to "Loading".
        """
        self.message = message
        # Moon phases sequence rotating clockwise
        self.spinner_chars = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
        self.stop_event = threading.Event()
        self.thread = None

    def _spin(self):
        """Internal animation loop executing in background thread."""
        idx = 0
        frames = [" .", " . -", " . - *", " *", " * -", " * - .", ""]
        max_len = max(len(f) for f in frames)

        # ANSI Colors for Esc prompt
        RED = "\033[1;31m"
        GRAY = "\033[38;5;244m"
        RESET = "\033[0m"
        esc_hint = f" {GRAY}({RED}Press [Esc] to cancel{GRAY}){RESET}"

        while not self.stop_event.is_set():
            # Check for Esc key press on Windows
            if os.name == 'nt':
                try:
                    import msvcrt
                    if msvcrt.kbhit():
                        ch = msvcrt.getch()
                        if ch in (b'\x1b', b'\x03'):  # ESC key or Ctrl+C
                            import _thread
                            self.stop_event.set()
                            try:
                                _cols = os.get_terminal_size().columns
                            except (ValueError, OSError):
                                _cols = 120
                            sys.stdout.write("\r" + " " * _cols + "\r")
                            sys.stdout.flush()
                            _thread.interrupt_main()
                            break
                except Exception:
                    pass

            char = self.spinner_chars[idx % len(self.spinner_chars)]
            frame = frames[idx % len(frames)]
            pad = " " * (max_len - len(frame))
            sys.stdout.write(f"\r  [{char}] {self.message}{frame}{pad}{esc_hint} ")
            sys.stdout.flush()
            idx += 1
            self.stop_event.wait(0.25)

        try:
            cols = os.get_terminal_size().columns
        except (ValueError, OSError):
            cols = 120
        sys.stdout.write("\r" + " " * cols + "\r")
        sys.stdout.flush()

    def start(self):
        """Starts the spinner animation in a background thread."""
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self):
        """Stops the spinner animation and clears the line."""
        self.stop_event.set()
        if self.thread:
            try:
                self.thread.join(timeout=0.5)
            except Exception:
                pass


class StreamBorderRenderer:
    """
    Modern Border Stream Renderer with Real-time Lightweight Markdown Styler:
    Renders streamed agent responses live with sleek borders and formats
    Markdown headers, bold text, lists, and code blocks on the fly.
    """
    P1 = "\033[38;5;97m"    # Soft Muted Purple
    P2 = "\033[38;5;98m"    # Soft Lavender Purple
    P3 = "\033[38;5;140m"   # Soft Lilac Violet
    P4 = "\033[38;5;141m"   # Soft Light Violet Glow
    GOLD = "\033[1;38;5;220m"
    AMBER = "\033[1;38;5;214m"
    LILAC = "\033[1;38;5;184m"
    CYAN = "\033[1;36m"
    GREEN = "\033[38;5;120m"
    CODE_TEXT = "\033[38;5;153m"
    GRAY = "\033[38;5;244m"
    WHITE_BOLD = "\033[1;38;5;255m"
    WHITE = "\033[38;5;253m"
    RESET = "\033[0m"

    def __init__(self):
        self.started = False
        self.line_buffer = ""
        self.in_code_block = False
        self.code_lang = ""
        try:
            self.cols = min(os.get_terminal_size().columns, 85)
        except (ValueError, OSError):
            self.cols = 80

    def _style_inline(self, text: str) -> str:
        """Applies inline styles like **bold**, `code`, and [links]."""
        # Bold: **text** -> bold white
        text = re.sub(r'\*\*(.+?)\*\*', f'{self.WHITE_BOLD}\\1{self.RESET}{self.WHITE}', text)
        # Inline code: `code` -> soft green
        text = re.sub(r'`([^`]+)`', f'{self.GREEN}\\1{self.RESET}{self.WHITE}', text)
        # Links: [text](url) -> underlined blue
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', f'\033[4;38;5;75m\\1{self.RESET}{self.WHITE} ({self.GRAY}\\2{self.RESET}{self.WHITE})', text)
        return text

    def _style_line(self, line: str) -> str:
        """Transforms a complete line of markdown into styled terminal output."""
        stripped = line.strip()

        # Check for code fence
        if stripped.startswith("```"):
            if not self.in_code_block:
                self.in_code_block = True
                lang = stripped[3:].strip()
                lang_tag = f" [{lang}]" if lang else ""
                bar_len = max(self.cols - len(lang_tag) - 10, 8)
                return f"{self.P1}┌──{self.P2}{lang_tag}{self.P1}{'─' * bar_len}{self.RESET}"
            else:
                self.in_code_block = False
                bar_len = max(self.cols - 10, 8)
                return f"{self.P1}└──{'─' * bar_len}{self.RESET}"

        if self.in_code_block:
            # Code block line
            return f"{self.CODE_TEXT}{line}{self.RESET}"

        # Headers
        if line.startswith("# "):
            return f"{self.GOLD}{line[2:]}{self.RESET}"
        elif line.startswith("## "):
            return f"{self.AMBER}{line[3:]}{self.RESET}"
        elif line.startswith("### "):
            return f"{self.LILAC}{line[4:]}{self.RESET}"
        elif line.startswith("#### "):
            return f"{self.LILAC}{line[5:]}{self.RESET}"

        # Bullet points: - item, * item, + item
        if re.match(r'^\s*[-*+]\s+', line):
            prefix_spaces = len(line) - len(line.lstrip())
            item_text = re.sub(r'^\s*[-*+]\s+', '', line)
            indent = " " * prefix_spaces
            return f"{indent}{self.GOLD}•{self.RESET} {self.WHITE}{self._style_inline(item_text)}{self.RESET}"

        # Numbered list: 1. item
        m_num = re.match(r'^(\s*)(\d+\.)\s+(.*)$', line)
        if m_num:
            indent, num, rest = m_num.groups()
            return f"{indent}{self.CYAN}{num}{self.RESET} {self.WHITE}{self._style_inline(rest)}{self.RESET}"

        # Blockquote: > text
        if line.startswith("> "):
            return f"{self.GOLD}▌{self.RESET} {self.GRAY}{self._style_inline(line[2:])}{self.RESET}"

        # Horizontal rule: --- or ***
        if stripped in ("---", "***", "___") and len(stripped) >= 3:
            return f"{self.P1}{'─' * (self.cols - 8)}{self.RESET}"

        # Normal text with inline styling
        return f"{self.WHITE}{self._style_inline(line)}{self.RESET}"

    def on_token(self, delta: str):
        """Processes incoming stream chunks, styling lines with left border."""
        if not delta:
            return

        if not self.started:
            self.started = True
            header = " 🤖 Agent "
            bar_len = max(self.cols - len(header) - 3, 10)
            sys.stdout.write(f"\n{self.P4}╭─{self.RESET}{self.P3}{header}{self.RESET}{self.P1}{'─' * bar_len}{self.RESET}\n")
            sys.stdout.write(f"{self.P1}│{self.RESET} ")
            sys.stdout.flush()

        self.line_buffer += delta

        # Process all complete lines ending in \n
        while "\n" in self.line_buffer:
            line, self.line_buffer = self.line_buffer.split("\n", 1)
            styled_line = self._style_line(line)
            sys.stdout.write(f"{styled_line}\n{self.P1}│{self.RESET} ")
            sys.stdout.flush()

    def finish(self, duration: float = 0.0, usage_info: str = ""):
        """Flushes any remaining line buffer and prints the bottom border."""
        if not self.started:
            return

        if self.line_buffer:
            styled_line = self._style_line(self.line_buffer)
            sys.stdout.write(styled_line)
            self.line_buffer = ""

        footer = f" ⏱️ {duration:.2f}s{usage_info} "
        bar_len = max(self.cols - len(footer) - 3, 10)
        sys.stdout.write(f"\n{self.P4}╰─{self.RESET}{self.GRAY}{footer}{self.RESET}{self.P1}{'─' * bar_len}{self.RESET}\n\n")
        sys.stdout.flush()

    def finish_intermediate(self):
        """Flushes buffer and closes border for intermediate tool calling."""
        if not self.started:
            return

        if self.line_buffer:
            styled_line = self._style_line(self.line_buffer)
            sys.stdout.write(styled_line)
            self.line_buffer = ""

        bar_len = max(self.cols - 4, 10)
        sys.stdout.write(f"\n{self.P4}╰─{self.RESET}{self.P1}{'─' * bar_len}{self.RESET}\n")
        sys.stdout.flush()

    def render_fallback(self, content: str, duration: float = 0.0, usage_info: str = ""):
        """Renders the entire response in a styled border block if streaming was not used."""
        self.on_token(content)
        self.finish(duration, usage_info)


# Custom styles for the CLI prompt and autocomplete dropdown menu
custom_style = Style.from_dict({
    'prompt': 'fg:#00ff88 bold',                # Neon green for "You" text
    'pointer': 'fg:#00bfff bold',               # Cyan for "❯" pointer
    'confirm': 'fg:#5c6370 italic',             # Dim gray italic hint for confirmation prompt
    'completion-menu.completion': 'bg:#2c313c #abb2bf',  # Dark slate background, soft white text
    'completion-menu.completion.current': 'bg:#00ff88 #000000 bold',  # Neon green background, black text when highlighted
    'auto-suggest': 'fg:#5c6370 italic',        # Dim gray italic text for autosuggestions
})

_prompt_session = None


def get_prompt_session():
    """
    Lazily instantiates PromptSession to prevent NoConsoleScreenBufferError
    when running under non-interactive test harnesses.
    """
    global _prompt_session
    if _prompt_session is None:
        try:
            _prompt_session = PromptSession(style=custom_style, auto_suggest=AutoSuggestFromHistory())
        except Exception:
            from prompt_toolkit.output import DummyOutput
            _prompt_session = PromptSession(style=custom_style, auto_suggest=AutoSuggestFromHistory(), output=DummyOutput())
    return _prompt_session


def get_user_input(skills):
    """
    Shows an interactive styled prompt to the user with autocomplete for commands and skills.
    Handles Ctrl+C (KeyboardInterrupt) and Ctrl+D (EOFError) gracefully.

    Args:
        skills (list[dict]): List of dicts representing available skills, e.g. [{"name": ...}]

    Returns:
        str: The typed string, or "/exit" on Ctrl+D.
    """
    words = ['/help', '/sessions', '/new', '/switch', '/delete_session', '/history', '/plugin', '/exit', '/quit', '/search', '/model', '/readonly', '/diff', '/enter2confirm', '/pin', '/unpin', '/pins', '/export', '/clear', '/ls', '/cd', '/init-ai', '/max_tool_calls', '/usage']
    for s in skills:
        words.append(f"/{s['name']}")
    completer = PromptCompleter(words)
    ps = get_prompt_session()

    try:
        user_text = ps.prompt(
            HTML('<prompt>You</prompt><pointer> ❯ </pointer>'),
            completer=completer
        ).strip()

        if not user_text:
            return ""

        # Slash commands execute immediately without double enter confirmation
        if user_text.startswith('/'):
            return user_text

        # Require double Enter confirmation only when ENTER_2_CONFIRM is enabled
        if config.ENTER_2_CONFIRM:
            confirm_text = ps.prompt(
                HTML('<confirm>(Press Enter again to send to AI, or edit text)</confirm><pointer> ❯ </pointer>'),
                default=user_text,
                completer=completer
            ).strip()
            return confirm_text

        return user_text

    except KeyboardInterrupt:
        print("\nExiting...")
        return "/exit"  # Return exit command to shut down the session
    except EOFError:
        return "/exit"  # Return exit command to shut down the session


def print_banner(model_name, project_path):
    """
    Renders a colored ASCII moon logo on the left and Losna CLI details on the right.

    Args:
        model_name (str): Active OpenRouter model name.
        project_path (str): Current workspace directory path.
    """
    P1 = "\033[38;5;97m"                           # Soft Muted Purple
    P2 = "\033[38;5;98m"                           # Soft Lavender Purple
    P3 = "\033[38;5;140m"                          # Soft Lilac Violet
    P4 = "\033[38;5;141m"                          # Soft Light Violet Glow
    GOLD = "\033[38;5;220m"
    AMBER = "\033[38;5;214m"
    LIGHT_BLUE = "\033[1;38;5;75m"
    WHITE = "\033[38;5;253m"
    GRAY = "\033[38;5;244m"
    RESET = "\033[0m"

    # Logo: 🌒 Waxing Crescent with Smooth Soft Purple Gradient (97 -> 98 -> 140 -> 141)
    visual_logo = [
        f"        {P1}.{P2}%{P3}%{P4}%{GOLD}**.{RESET}        ",
        f"      {P1}%{P2}%o{P3}%%{P4}%%{GOLD}%**.{RESET}       ",
        f"     {P1}%%{P2}%%{P3}0%{P4}%%%{AMBER}%%*{GOLD}*{RESET}      ",
        f"    {P1}##{P2}##{P3}o#{P4}#####{AMBER}%+{GOLD}**{RESET}     ",
        f"    {P1}##{P2}###{P3}#{P4}0####{AMBER}%+{GOLD}**{RESET}     ",
        f"     {P1}%%{P2}%%{P3}o%{P4}%%%{AMBER}%%*{GOLD}*{RESET}      ",
        f"      {P1}%{P2}%%{P3}%%{P4}%%%{GOLD}%**{RESET}      ",
        f"        {P1}'{P2}%{P3}%{P4}%{GOLD}**'{RESET}        ",
    ]
    # Text lines on the right side
    text_lines = [
        "",
        "",
        f"{LIGHT_BLUE}Losna CLI {config.VERSION}{RESET}",
        f"{WHITE}{model_name}{RESET}",
        f"{GRAY}{project_path}{RESET}",
    ]

    # Print side-by-side
    for i in range(len(visual_logo)):
        right_text = text_lines[i] if i < len(text_lines) else ""
        print(f"{visual_logo[i]}   {right_text}")
    print()


def print_session_header(session_id: int):
    """
    Renders banner, current session ID, auto-loaded context notice, and command hints.

    Args:
        session_id (int): Active session database ID.
    """
    from . import prompts
    model_display = "Deepseek V4 flash" if "deepseek-v4-flash" in config.MODEL_NAME else config.MODEL_NAME.split("/")[-1].replace("-", " ").title()
    project_path = os.path.realpath(os.getcwd()).replace("\\", "/")
    print_banner(model_display, project_path)
    print(f"Current session: [{session_id}]")
    auto_fname, auto_fpath, _ = prompts.load_auto_ai_context()
    if auto_fname:
        print(f"  \033[1;36m[System]: Auto-loaded project AI instructions from '{auto_fname}' ({auto_fpath})\033[0m")
    print("Commands: '/new <title>' new chat | '/switch <id>' change chat | '@file' attach file | '/ls' list dir | '/cd' change dir | '/init-ai' init blueprint | '/help' help menu | '/exit' or '/quit' to leave.\n")

    # Trigger update checker in a non-blocking background thread
    _trigger_async_update_check()


def _trigger_async_update_check():
    """
    Spawns a background thread to check for updates against the GitHub repository.
    Never blocks the main program startup.
    """
    import urllib.request
    from . import skills_loader
    # json is imported at module level

    GREEN = "\033[38;5;120m"
    GRAY = "\033[38;5;244m"
    LIGHT_BLUE = "\033[1;38;5;75m"
    RESET = "\033[0m"

    project_root = skills_loader._project_root()
    global_dir = os.path.expanduser("~/.losna")
    cache_file = os.path.join(global_dir, "update_cache.json")

    local_git_dir = os.path.join(global_dir, ".git")
    if not os.path.exists(local_git_dir):
        local_git_dir = os.path.join(project_root, ".git")

    if not os.path.exists(local_git_dir):
        return

    def check_github():
        local_sha = None
        try:
            head_path = os.path.join(local_git_dir, "HEAD")
            with open(head_path, "r") as f:
                ref = f.read().strip()
            if ref.startswith("ref:"):
                ref_path = os.path.join(local_git_dir, ref.split(" ")[1])
                with open(ref_path, "r") as f:
                    local_sha = f.read().strip()
            else:
                local_sha = ref
        except Exception:
            return

        if not local_sha:
            return

        now = time.time()
        cached_sha = None
        last_check = 0

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    cached_sha = data.get("remote_sha")
                    last_check = data.get("last_check", 0)
            except Exception:
                pass

        if now - last_check < 21600 and cached_sha:
            remote_sha = cached_sha
        else:
            try:
                url = "https://api.github.com/repos/snui1s/losna-cli/commits/main"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LosnaCLIUpdater"}
                )
                with urllib.request.urlopen(req, timeout=3.0) as response:
                    res_data = json.loads(response.read().decode())
                    remote_sha = res_data.get("sha")

                os.makedirs(global_dir, exist_ok=True)
                with open(cache_file, "w") as f:
                    json.dump({"remote_sha": remote_sha, "last_check": now}, f)
            except Exception:
                remote_sha = cached_sha

        if remote_sha and local_sha != remote_sha:
            print(f"\n  {GREEN}✨ A new version of Losna CLI is available!{RESET}")
            if os.name == 'nt':
                print(f"  {GRAY}Run this in PowerShell to update:{RESET}")
                print(f"  {LIGHT_BLUE}irm https://raw.githubusercontent.com/snui1s/losna-cli/main/install.ps1 | iex{RESET}\n")
            else:
                print(f"  {GRAY}Run this in Terminal to update:{RESET}")
                print(f"  {LIGHT_BLUE}curl -sSL https://raw.githubusercontent.com/snui1s/losna-cli/main/install.sh | bash{RESET}\n")

    threading.Thread(target=check_github, daemon=True).start()


def print_agent_response(content: str, duration: float, usage_info: str = ""):
    """
    Renders the agent's markdown response beautifully using Rich.

    Args:
        content (str): Markdown response text to render.
        duration (float): Response generation duration in seconds.
        usage_info (str, optional): Additional token usage details to append to panel title.
    """
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.theme import Theme
    from rich import box

    custom_theme = Theme({
        "markdown.h1": "bold color(220)",      # Bright Gold
        "markdown.h2": "bold color(214)",      # Amber / Orange-yellow
        "markdown.h3": "bold color(184)",      # Yellowish-green / Soft Gold
        "markdown.h4": "bold color(184)",
        "markdown.h5": "bold color(184)",
        "markdown.h6": "bold color(184)",
        "markdown.item.bullet": "color(220)",  # Gold bullets
        "markdown.block": "color(220)",        # Vertical border bar of blockquote
        "markdown.blockquote": "color(186)",   # Controls quote block text
        "markdown.paragraph": "color(253)",    # Default body paragraph text
        "markdown.hr": "color(214)",           # Horizontal rule divider line
    })

    console = Console(theme=custom_theme)
    console.print()

    title_text = f"Agent (took {duration:.2f}s{usage_info})"
    md = Markdown(content)
    panel = Panel(
        md,
        title=f"[bold color(141)]{title_text}[/bold color(141)]",
        title_align="left",
        border_style="color(97)",              # Soft cosmic purple border
        box=box.ROUNDED,
        padding=(1, 2)
    )

    console.print(panel)
    console.print()
