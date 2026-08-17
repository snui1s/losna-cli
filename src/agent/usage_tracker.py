"""
usage_tracker.py — In-memory token usage and cost accumulator for Losna CLI.

Tracks prompt tokens, completion tokens, and cost across API calls
within a single program session. No database persistence — lightweight and fast.
"""


class UsageTracker:
    """Accumulates token usage and cost across multiple OpenRouter API calls."""

    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0

    def record(self, prompt_tokens=0, completion_tokens=0, cost=0.0):
        """
        Record one API call's usage stats.

        Args:
            prompt_tokens (int): Number of prompt/input tokens.
            completion_tokens (int): Number of completion/output tokens.
            cost (float): Cost in USD for this call.
        """
        self.total_prompt_tokens += prompt_tokens or 0
        self.total_completion_tokens += completion_tokens or 0
        self.total_cost += cost or 0.0
        self.call_count += 1

    @property
    def total_tokens(self):
        return self.total_prompt_tokens + self.total_completion_tokens

    def format_summary(self):
        """
        Full usage summary for /usage command.

        Returns:
            str: Multi-line formatted summary string.
        """
        CYAN = "\033[1;36m"
        GREEN = "\033[1;32m"
        GOLD = "\033[1;33m"
        GRAY = "\033[38;5;244m"
        RESET = "\033[0m"

        cost_str = f"${self.total_cost:.4f}" if self.total_cost > 0 else "N/A (free model)"

        lines = [
            f"{GOLD}═══ Session Token Usage ═══{RESET}",
            f"  {GRAY}API calls:{RESET}          {CYAN}{self.call_count}{RESET}",
            f"  {GRAY}Prompt tokens:{RESET}      {CYAN}{self.total_prompt_tokens:,}{RESET}",
            f"  {GRAY}Completion tokens:{RESET}   {CYAN}{self.total_completion_tokens:,}{RESET}",
            f"  {GRAY}Total tokens:{RESET}        {GREEN}{self.total_tokens:,}{RESET}",
            f"  {GRAY}Estimated cost:{RESET}      {GREEN}{cost_str}{RESET}",
            f"{GOLD}═══════════════════════════{RESET}",
        ]
        return "\n".join(lines)

    def format_exit_summary(self):
        """
        Compact exit summary shown when the program terminates.

        Returns:
            str: Formatted exit summary string, or empty string if no calls were made.
        """
        if self.call_count == 0:
            return ""

        GOLD = "\033[1;33m"
        CYAN = "\033[1;36m"
        GREEN = "\033[1;32m"
        GRAY = "\033[38;5;244m"
        RESET = "\033[0m"

        cost_str = f"${self.total_cost:.4f}" if self.total_cost > 0 else "free"
        return (
            f"\n{GOLD}📊 Session Summary:{RESET} "
            f"{CYAN}{self.call_count}{RESET} API calls · "
            f"{GREEN}{self.total_tokens:,}{RESET} tokens "
            f"{GRAY}({self.total_prompt_tokens:,} in / {self.total_completion_tokens:,} out){RESET} · "
            f"{GREEN}{cost_str}{RESET}\n"
        )
