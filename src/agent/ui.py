import threading
import sys
import time
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

class SlashCompleter(Completer):
    """Only suggests completions when input starts with '/'."""
    def __init__(self, commands):
        self.commands = sorted(commands)

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.lstrip()
        if not text.startswith('/'):
            return
        for cmd in self.commands:
            if cmd.startswith(text):
                yield Completion(cmd, start_position=-len(text))

class Spinner:
    def __init__(self, message="Loading"):
        self.message = message
        # Moon phases sequence rotating clockwise
        self.spinner_chars = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
        self.stop_event = threading.Event()
        self.thread = None

    def _spin(self):
        idx = 0
        # Traveling wave: builds up, peak shifts, trails off, then resets
        frames = [" .", " . -", " . - *", " *", " * -", " * - .", ""]
        max_len = max(len(f) for f in frames)
        while not self.stop_event.is_set():
            char = self.spinner_chars[idx % len(self.spinner_chars)]
            frame = frames[idx % len(frames)]
            pad = " " * (max_len - len(frame))
            sys.stdout.write(f"\r  [{char}] {self.message}{frame}{pad} ")
            sys.stdout.flush()
            idx += 1
            self.stop_event.wait(0.25)
        # Clean up line
        sys.stdout.write("\r" + " " * 50 + "\r")
        sys.stdout.flush()

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()

# Custom styles for the CLI prompt and autocomplete dropdown menu
custom_style = Style.from_dict({
    'prompt': 'fg:#00ff88 bold',                # Neon green for "You" text
    'pointer': 'fg:#00bfff bold',               # Cyan for "❯" pointer
    'completion-menu.completion': 'bg:#2c313c #abb2bf', # Dark slate background, soft white text
    'completion-menu.completion.current': 'bg:#00ff88 #000000 bold', # Neon green background, black text when highlighted
    'auto-suggest': 'fg:#5c6370 italic',        # Dim gray italic text for autosuggestions
})

# Instantiate the PromptSession once at the module level with auto_suggest enabled
prompt_session = PromptSession(style=custom_style, auto_suggest=AutoSuggestFromHistory())

def get_user_input(skills):
    """
    Shows an interactive styled prompt to the user with autocomplete for commands and skills.
    Handles Ctrl+C (KeyboardInterrupt) and Ctrl+D (EOFError) gracefully.
    Args:
        skills: List of dicts representing available skills, e.g. [{"name": ...}]
    Returns the typed string, or "/exit" on Ctrl+D.
    """
    words = ['/help', '/sessions', '/new', '/switch', '/exit', '/quit']
    for s in skills:
        words.append(f"/{s['name']}")
    completer = SlashCompleter(words)

    try:
        return prompt_session.prompt(
            HTML('<prompt>You</prompt><pointer> ❯ </pointer>'),
            completer=completer
        ).strip()
    except KeyboardInterrupt:
        print("\nExiting...")
        return "/exit"  # Return exit command to shut down the session
    except EOFError:
        return "/exit"  # Return exit command to shut down the session

def print_banner(model_name, project_path):
    """
    Renders a colored ASCII moon logo on the left and Losna CLI details on the right.
    """
    # ANSI color codes
    GOLD = "\033[38;5;220m"
    AMBER = "\033[38;5;214m"
    PURPLE = "\033[38;5;97m"                      # Soft cosmic purple for the dark side
    LIGHT_BLUE = "\033[1;38;5;75m"
    WHITE = "\033[38;5;253m"
    GRAY = "\033[38;5;244m"
    RESET = "\033[0m"

    # Logo: 🌒 Waxing Crescent (Sharp Double Tips) - แหลมคมทั้งยอดบนและยอดล่าง สมมาตรกลมมน
    visual_logo = [
        f"        {PURPLE}.%%%%{GOLD}**.{RESET}        ",
        f"      {PURPLE}%%o%%%%%{GOLD}%**.{RESET}       ",
        f"     {PURPLE}%%%%%0%%%%{AMBER}%%*{GOLD}*{RESET}      ",
        f"    {PURPLE}####o#######{AMBER}%+{GOLD}**{RESET}     ",
        f"    {PURPLE}#######0####{AMBER}%+{GOLD}**{RESET}     ",
        f"     {PURPLE}%%%%o%%%%%{AMBER}%%*{GOLD}*{RESET}      ",
        f"      {PURPLE}%%%%%%%%%{GOLD}%**{RESET}      ",
        f"        {PURPLE}'%%%%{GOLD}**'{RESET}        ",
    ]
    # Text lines on the right side (vertically centered with the moon)
    text_lines = [
        "",
        "",
        f"{LIGHT_BLUE}Losna CLI 0.1.0{RESET}",
        f"{WHITE}{model_name}{RESET}",
        f"{GRAY}{project_path}{RESET}",
    ]

    # Print side-by-side
    for i in range(len(visual_logo)):
        right_text = text_lines[i] if i < len(text_lines) else ""
        print(f"{visual_logo[i]}   {right_text}")
    print()


def print_agent_response(content: str, duration: float):
    """
    Renders the agent's markdown response beautifully using rich.
    Includes an elegant header box and handles syntaxes/tables nicely.
    """
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.theme import Theme
    from rich.live import Live

    # Define custom styling theme for Markdown elements
    # Using gold/yellow tones for headings, blockquotes, and dividers instead of dark purple
    custom_theme = Theme({
        "markdown.h1": "bold color(220)",      # Bright Gold
        "markdown.h2": "bold color(214)",      # Amber / Orange-yellow
        "markdown.h3": "bold color(184)",      # Yellowish-green / Soft Gold
        "markdown.h4": "bold color(184)",
        "markdown.h5": "bold color(184)",
        "markdown.h6": "bold color(184)",
        "markdown.item.bullet": "color(220)",  # Gold bullets
        "markdown.block": "color(220)",        # This controls the vertical border bar color of blockquote (Gold)
        "markdown.blockquote": "color(186)",   # Controls the quote block text wrapper (Soft yellow)
        "markdown.paragraph": "color(253)",    # Default body paragraph text (Soft white)
        "markdown.hr": "color(214)",           # Horizontal rule divider line in Amber/Gold
    })

    # The console MUST be initialized with this theme, and used throughout
    console = Console(theme=custom_theme)
    
    console.print()
    
    # We gradually construct the text by characters (or words) to render dynamically
    words = content.split(" ")
    current_text = ""
    
    # Helper to generate Markdown instances that automatically read our console's styles
    def get_md(text: str) -> Markdown:
        return Markdown(text)
    
    # Create the Live container using a panel with initially empty markdown
    # Pass the themed console so it inherits styles correctly
    panel = Panel(
        get_md(current_text),
        title=f"[bold yellow]Agent (took {duration:.2f}s)[/bold yellow]",
        title_align="left",
        border_style="bold color(214)",        # Change frame border from cyan to bold amber/yellow
        padding=(1, 2)
    )
    
    with Live(panel, console=console, refresh_per_second=20, transient=False) as live:
        # Dynamically build up the response
        i = 0
        step = max(1, len(words) // 250)  # Adjust chunk size so long responses don't type too slowly
        while i < len(words):
            current_text = " ".join(words[:i+step])
            panel.renderable = get_md(current_text)
            live.update(panel)
            i += step
            time.sleep(0.015)
        
        # Ensure the final render shows the 100% complete content
        panel.renderable = get_md(content)
        live.update(panel)
        
    console.print()
