"""
ui.py — Terminal User Interface (TUI) and output rendering module.

Provides prompt_toolkit session wrappers with autocomplete, Rich-based markdown
response rendering, ASCII banner display, and non-blocking background update checks.
"""

import threading
import sys
import time
import os
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

                count = 0
                for root, dirs, files in os.walk(base_dir):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
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
                    if ".." .startswith(search_prefix.lower()):
                        candidates.append("..")

                    for item in sorted(os.listdir(target_dir)):
                        if item.startswith(".") and item not in [".env", ".losnarc"]:
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
                            sys.stdout.write("\r" + " " * 80 + "\r")
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

        sys.stdout.write("\r" + " " * 80 + "\r")
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
    words = ['/help', '/sessions', '/new', '/switch', '/delete_session', '/history', '/plugin', '/exit', '/quit', '/search', '/model', '/readonly', '/diff', '/enter2confirm', '/pin', '/unpin', '/pins', '/export', '/clear', '/ls', '/cd', '/max_tool_calls']
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

    # Trigger update checker in a non-blocking background thread
    _trigger_async_update_check()


def _trigger_async_update_check():
    """
    Spawns a background thread to check for updates against the GitHub repository.
    Never blocks the main program startup.
    """
    import urllib.request
    from . import skills_loader

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


def print_agent_response(content: str, duration: float):
    """
    Renders the agent's markdown response beautifully using Rich.

    Args:
        content (str): Markdown response text to render.
        duration (float): Response generation duration in seconds.
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

    md = Markdown(content)
    panel = Panel(
        md,
        title=f"[bold color(141)]Agent (took {duration:.2f}s)[/bold color(141)]",
        title_align="left",
        border_style="color(97)",              # Soft cosmic purple border
        box=box.ROUNDED,
        padding=(1, 2)
    )

    console.print(panel)
    console.print()
