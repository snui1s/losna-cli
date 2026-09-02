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
import unicodedata

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
from prompt_toolkit.key_binding import KeyBindings
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
    Threaded terminal progress spinner with rotating moon phase indicators,
    live elapsed timer, and dynamic status updates.
    """

    def __init__(self, message="Loading", show_timer=False, auto_status=False):
        """
        Initializes the spinner instance.

        Args:
            message (str, optional): Loading text label. Defaults to "Loading".
            show_timer (bool, optional): Whether to display elapsed seconds. Defaults to False.
            auto_status (bool, optional): Whether to auto-update status message on long delays. Defaults to False.
        """
        self.message = message
        self.show_timer = show_timer
        self.auto_status = auto_status
        self.start_time = time.time()
        self.diagnostic_tag = ""
        self.lock = threading.Lock()
        # Moon phases sequence rotating clockwise
        self.spinner_chars = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
        self.stop_event = threading.Event()
        self.thread = None

    def update_message(self, new_message: str):
        """Thread-safe update for the spinner status message."""
        with self.lock:
            self.message = new_message

    def set_diagnostic_tag(self, tag: str):
        """Thread-safe update for an extra diagnostic badge/tag."""
        with self.lock:
            self.diagnostic_tag = tag

    def _spin(self):
        """Internal animation loop executing in background thread."""
        idx = 0
        frames = [" .", " . -", " . - *", " *", " * -", " * - .", ""]
        max_len = max(len(f) for f in frames)

        # ANSI Colors for Esc prompt
        RED = "\033[1;31m"
        GRAY = "\033[38;5;244m"
        YELLOW = "\033[1;33m"
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

            elapsed = int(time.time() - self.start_time)
            with self.lock:
                current_msg = self.message
                diag_tag = self.diagnostic_tag

            if self.auto_status:
                if elapsed >= 25:
                    current_msg = f"{YELLOW}Upstream model is taking longer than usual{RESET}"
                elif elapsed >= 10:
                    current_msg = "Waiting for model response"

            timer_str = f" {GRAY}({elapsed}s){RESET}" if (self.show_timer and elapsed >= 1) else ""
            tag_str = f" {diag_tag}" if diag_tag else ""

            char = self.spinner_chars[idx % len(self.spinner_chars)]
            frame = frames[idx % len(frames)]
            pad = " " * (max_len - len(frame))
            sys.stdout.write(f"\r  [{char}] {current_msg}{timer_str}{tag_str}{frame}{pad}{esc_hint} ")
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
        self.start_time = time.time()
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
    Modern Border Stream Renderer with Real-time Markdown Styler & Table Auto-Aligner:
    Renders streamed agent responses live with sleek borders, formats Markdown
    headers, bold text, lists, and code blocks, and auto-aligns Markdown tables into
    Unicode box-drawing tables.
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
        self.table_buffer = []
        try:
            self.cols = min(os.get_terminal_size().columns, 85)
        except (ValueError, OSError):
            self.cols = 80

    def _strip_markdown(self, text: str) -> str:
        """Removes inline markdown delimiters for accurate visual length measurement."""
        text = re.sub(r'\033\[[0-9;]*m', '', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        return text

    def _display_width(self, text: str) -> int:
        """Calculates visual terminal width handling Thai combining vowels, emojis, and inline markdown."""
        clean = self._strip_markdown(text)
        w = 0
        for ch in clean:
            cat = unicodedata.category(ch)
            if cat in ('Mn', 'Me', 'Cf'):  # Combining marks (Thai vowels/tones)
                continue
            eaw = unicodedata.east_asian_width(ch)
            if eaw in ('W', 'F'):
                w += 2
            else:
                w += 1
        return w

    def _wrap_cell_text(self, text: str, max_w: int) -> list[str]:
        """Wraps cell text across multiple lines so each line visual width <= max_w."""
        if not text:
            return [""]
        if self._display_width(text) <= max_w:
            return [text]

        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            if not current_line:
                if self._display_width(word) > max_w:
                    chunk = ""
                    for ch in word:
                        ch_w = 0 if unicodedata.category(ch) in ('Mn', 'Me', 'Cf') else (2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1)
                        if self._display_width(chunk) + ch_w > max_w:
                            lines.append(chunk)
                            chunk = ch
                        else:
                            chunk += ch
                    current_line = chunk
                else:
                    current_line = word
            else:
                candidate = f"{current_line} {word}"
                if self._display_width(candidate) <= max_w:
                    current_line = candidate
                else:
                    lines.append(current_line)
                    if self._display_width(word) > max_w:
                        chunk = ""
                        for ch in word:
                            ch_w = 0 if unicodedata.category(ch) in ('Mn', 'Me', 'Cf') else (2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1)
                            if self._display_width(chunk) + ch_w > max_w:
                                lines.append(chunk)
                                chunk = ch
                            else:
                                chunk += ch
                        current_line = chunk
                    else:
                        current_line = word

        if current_line:
            lines.append(current_line)

        return lines or [""]

    def _pad_to_width(self, text: str, target_width: int) -> str:
        """Pads string with spaces to reach exact visual terminal width."""
        w = self._display_width(text)
        return text + " " * max(0, target_width - w)

    def _is_table_row(self, line: str) -> bool:
        """Checks if line looks like a markdown table row."""
        stripped = line.strip()
        return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2

    def _is_table_separator(self, line: str) -> bool:
        """Checks if line is a markdown table separator like |---|---|."""
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            return False
        cells = [c.strip() for c in stripped[1:-1].split("|")]
        return all(re.match(r'^:?-+:?$', c) for c in cells if c)

    def _render_table(self, rows: list[str]) -> list[str]:
        """Parses raw markdown table rows and renders a beautiful aligned Unicode box table with multi-line cell wrapping."""
        parsed_rows = []
        has_separator = False

        for r in rows:
            if self._is_table_separator(r):
                has_separator = True
                continue
            cells = [c.strip() for c in r.strip()[1:-1].split("|")]
            parsed_rows.append(cells)

        if not parsed_rows:
            return rows

        num_cols = max(len(r) for r in parsed_rows)
        for r in parsed_rows:
            while len(r) < num_cols:
                r.append("")

        # Calculate natural max width per column
        col_widths = [4] * num_cols
        for r in parsed_rows:
            for i, cell in enumerate(r):
                col_widths[i] = max(col_widths[i], self._display_width(cell))

        # Dynamically determine max table width based on current terminal size
        try:
            current_term_cols = os.get_terminal_size().columns
        except (ValueError, OSError):
            current_term_cols = self.cols
        max_table_width = max(current_term_cols - 6, 30)

        # Check if table exceeds max_table_width and adjust proportionally
        overhead = 1 + num_cols * 3  # Borders and cell padding: '│ ' and ' │'
        total_needed = sum(col_widths) + overhead

        if total_needed > max_table_width:
            avail_budget = max_table_width - overhead
            min_w = 6
            if avail_budget < num_cols * min_w:
                avail_budget = num_cols * min_w

            allocated = [min_w] * num_cols
            rem_budget = avail_budget - (num_cols * min_w)

            excess_widths = [max(0, w - min_w) for w in col_widths]
            total_excess = sum(excess_widths)

            if total_excess > 0:
                for i in range(num_cols):
                    add_w = int(rem_budget * (excess_widths[i] / total_excess))
                    allocated[i] += add_w
                diff = avail_budget - sum(allocated)
                if diff > 0:
                    widest_indices = sorted(range(num_cols), key=lambda idx: col_widths[idx], reverse=True)
                    for k in range(min(diff, num_cols)):
                        allocated[widest_indices[k]] += 1
                col_widths = allocated
            else:
                col_widths = [max(min_w, avail_budget // num_cols)] * num_cols

        top_border = f"{self.P1}┌" + "┬".join("─" * (w + 2) for w in col_widths) + f"┐{self.RESET}"
        mid_border = f"{self.P1}├" + "┼".join("─" * (w + 2) for w in col_widths) + f"┤{self.RESET}"
        bot_border = f"{self.P1}└" + "┴".join("─" * (w + 2) for w in col_widths) + f"┘{self.RESET}"

        rendered = [top_border]

        for row_idx, r in enumerate(parsed_rows):
            is_header = (row_idx == 0 and has_separator)

            # Wrap each cell in this row into multi-line chunks
            wrapped_cells = [self._wrap_cell_text(cell, col_widths[i]) for i, cell in enumerate(r)]
            max_sublines = max(len(w_cell) for w_cell in wrapped_cells)

            for sub_idx in range(max_sublines):
                formatted_cells = []
                for i in range(num_cols):
                    sub_text = wrapped_cells[i][sub_idx] if sub_idx < len(wrapped_cells[i]) else ""
                    styled_sub = self._style_inline(sub_text)
                    padded = self._pad_to_width(styled_sub, col_widths[i])
                    if is_header:
                        formatted_cells.append(f" {self.GOLD}{padded}{self.RESET} ")
                    else:
                        formatted_cells.append(f" {self.WHITE}{padded}{self.RESET} ")

                row_line = f"{self.P1}│{self.RESET}" + f"{self.P1}│{self.RESET}".join(formatted_cells) + f"{self.P1}│{self.RESET}"
                rendered.append(row_line)

            if is_header:
                rendered.append(mid_border)

        rendered.append(bot_border)
        return rendered

    def _flush_table_buffer(self):
        """Flushes buffered table rows to stdout as a styled box table."""
        if not self.table_buffer:
            return
        rendered_lines = self._render_table(self.table_buffer)
        self.table_buffer = []
        for line in rendered_lines:
            sys.stdout.write(f"{line}\n{self.P1}│{self.RESET} ")
        sys.stdout.flush()

    def _style_inline(self, text: str) -> str:
        """Applies inline styles like **bold**, `code`, and [links], cleanly removing raw delimiters."""
        # Bold: **text** or __text__ -> bold white
        text = re.sub(r'\*\*(.+?)\*\*', f'{self.WHITE_BOLD}\\1{self.RESET}{self.WHITE}', text)
        text = re.sub(r'__(.+?)__', f'{self.WHITE_BOLD}\\1{self.RESET}{self.WHITE}', text)
        # Italic / Single asterisk: *text* -> bold white
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', f'{self.WHITE_BOLD}\\1{self.RESET}{self.WHITE}', text)
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
        if stripped.startswith("# "):
            header_text = self._strip_markdown(stripped[2:])
            return f"{self.GOLD}{header_text}{self.RESET}"
        elif stripped.startswith("## "):
            header_text = self._strip_markdown(stripped[3:])
            return f"{self.AMBER}{header_text}{self.RESET}"
        elif stripped.startswith("### "):
            header_text = self._strip_markdown(stripped[4:])
            return f"{self.LILAC}{header_text}{self.RESET}"
        elif stripped.startswith("#### "):
            header_text = self._strip_markdown(stripped[5:])
            return f"{self.LILAC}{header_text}{self.RESET}"

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

        # Blockquote: > text or empty >
        if stripped.startswith(">"):
            quote_text = stripped[1:].lstrip()
            if not quote_text:
                return f"{self.GOLD}▌{self.RESET}"
            return f"{self.GOLD}▌{self.RESET} {self.WHITE}{self._style_inline(quote_text)}{self.RESET}"

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

            # Table row handling
            if self._is_table_row(line) or self._is_table_separator(line):
                self.table_buffer.append(line)
            else:
                self._flush_table_buffer()
                styled_line = self._style_line(line)
                sys.stdout.write(f"{styled_line}\n{self.P1}│{self.RESET} ")
                sys.stdout.flush()

    def finish(self, duration: float = 0.0, usage_info: str = ""):
        """Flushes any remaining line buffer and prints the bottom border."""
        if not self.started:
            return

        if self.line_buffer:
            if self._is_table_row(self.line_buffer) or self._is_table_separator(self.line_buffer):
                self.table_buffer.append(self.line_buffer)
            else:
                self._flush_table_buffer()
                styled_line = self._style_line(self.line_buffer)
                sys.stdout.write(styled_line)
            self.line_buffer = ""

        self._flush_table_buffer()

        footer = f" ⏱️ {duration:.2f}s{usage_info} "
        bar_len = max(self.cols - len(footer) - 3, 10)
        sys.stdout.write(f"\n{self.P4}╰─{self.RESET}{self.GRAY}{footer}{self.RESET}{self.P1}{'─' * bar_len}{self.RESET}\n\n")
        sys.stdout.flush()

    def finish_intermediate(self):
        """Flushes buffer and closes border for intermediate tool calling."""
        if not self.started:
            return

        if self.line_buffer:
            if self._is_table_row(self.line_buffer) or self._is_table_separator(self.line_buffer):
                self.table_buffer.append(self.line_buffer)
            else:
                self._flush_table_buffer()
                styled_line = self._style_line(self.line_buffer)
                sys.stdout.write(styled_line)
            self.line_buffer = ""

        self._flush_table_buffer()

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


def create_prompt_keybindings():
    """
    Creates keybindings for PromptSession:
    - Tab: Accepts autosuggestion (ghost text) if available, or navigates/applies completion.
    - Shift+Tab: Navigates to previous completion item.
    - Right Arrow: Accepts autosuggestion when at end of input.
    """
    kb = KeyBindings()

    @kb.add('tab')
    def _handle_tab(event):
        b = event.current_buffer
        if b.complete_state:
            b.complete_next()
        elif b.suggestion:
            b.insert_text(b.suggestion.text)
        else:
            b.start_completion(select_first=True)

    @kb.add('s-tab')
    def _handle_shift_tab(event):
        b = event.current_buffer
        if b.complete_state:
            b.complete_previous()

    @kb.add('right')
    def _handle_right(event):
        b = event.current_buffer
        if b.cursor_position == len(b.text) and b.suggestion:
            b.insert_text(b.suggestion.text)
        else:
            b.cursor_right()

    return kb


_prompt_keybindings = create_prompt_keybindings()


def get_prompt_session():
    """
    Lazily instantiates PromptSession to prevent NoConsoleScreenBufferError
    when running under non-interactive test harnesses.
    """
    global _prompt_session
    if _prompt_session is None:
        try:
            _prompt_session = PromptSession(
                style=custom_style,
                auto_suggest=AutoSuggestFromHistory(),
                key_bindings=_prompt_keybindings,
                complete_while_typing=True
            )
        except Exception:
            from prompt_toolkit.output import DummyOutput
            _prompt_session = PromptSession(
                style=custom_style,
                auto_suggest=AutoSuggestFromHistory(),
                key_bindings=_prompt_keybindings,
                complete_while_typing=True,
                output=DummyOutput()
            )
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
    words = [
        '/help', '/sessions', '/new', '/rename',
        '/switch', '/delete_session', '/history', '/plugin', '/exit', '/quit',
        '/search', '/model', '/readonly', '/diff', '/enter2confirm',
        '/pin', '/unpin', '/pins', '/export', '/clear', '/ls', '/cd',
        '/init-ai', '/max_tool_calls', '/usage'
    ]
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
            with open(head_path, "r", encoding="utf-8", errors="ignore") as f:
                ref = f.read().strip()
            if ref.startswith("ref:"):
                ref_subpath = ref.split(" ", 1)[1].strip()
                ref_path = os.path.join(local_git_dir, ref_subpath)
                if os.path.exists(ref_path):
                    with open(ref_path, "r", encoding="utf-8", errors="ignore") as f:
                        local_sha = f.read().strip()
                else:
                    packed_path = os.path.join(local_git_dir, "packed-refs")
                    if os.path.exists(packed_path):
                        with open(packed_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith("#") and not line.startswith("^"):
                                    parts = line.split(" ")
                                    if len(parts) >= 2 and parts[1] == ref_subpath:
                                        local_sha = parts[0]
                                        break
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


def print_recent_messages_preview(messages: list[dict], session_id=None, session_title=None):
    """
    Renders a compact, beautifully styled preview box of recent messages in the session.

    Args:
        messages (list[dict]): List of recent message dicts ({'role': 'user'|'assistant', 'content': str}).
        session_id (int, optional): Session database ID.
        session_title (str, optional): Session title string.
    """
    if not messages:
        return

    GREEN = "\033[1;32m"
    GOLD = "\033[38;5;220m"
    GRAY = "\033[38;5;244m"
    DARK_GRAY = "\033[38;5;238m"
    RESET = "\033[0m"

    title_part = f"Session [{session_id}]" if session_id else "Recent Conversation"
    if session_title:
        title_part += f" '{session_title}'"

    try:
        term_width = os.get_terminal_size().columns
    except (ValueError, OSError):
        term_width = 80
    term_width = min(max(term_width, 60), 100)

    header_text = f" 💬 Recent Messages in {title_part} "
    dash_count = max(4, term_width - len(header_text) - 4)
    top_border = f"{DARK_GRAY}┌─{GOLD}{header_text}{DARK_GRAY}{'─' * dash_count}┐{RESET}"
    bottom_border = f"{DARK_GRAY}└{'─' * (term_width - 2)}┘{RESET}"

    print(top_border)
    for m in messages:
        role = m.get("role", "").lower()
        content = (m.get("content") or "").strip()
        if not content:
            continue

        first_line = content.splitlines()[0].strip()
        max_content_len = term_width - 18
        if len(first_line) > max_content_len:
            first_line = first_line[:max_content_len - 3] + "..."
        elif len(content.splitlines()) > 1 and len(first_line) < max_content_len - 5:
            first_line += " ..."

        if role == "user":
            role_badge = f"{GREEN}🧑 You:{RESET}"
        elif role == "assistant":
            role_badge = f"{GOLD}🌒 Losna:{RESET}"
        else:
            role_badge = f"{GRAY}[{role.title()}]:{RESET}"

        print(f"{DARK_GRAY}│{RESET}  {role_badge} {first_line}")
    print(bottom_border)
    print()
