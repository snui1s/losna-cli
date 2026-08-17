"""
agent_loop.py — OpenRouter streaming API loop with tool dispatch for Losna CLI.

Handles the core AI conversation loop: streaming responses, accumulating tool calls,
executing tools with confirmation dialogs, and persisting results to SQLite.
"""

import sys
import time
import json
from openrouter import OpenRouter
from . import config
from . import db
from . import diff_utils
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme
from rich.live import Live
from rich import box
from .tools import dispatch_tool, get_available_tools
from .ui import Spinner, print_agent_response

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


# ────────────────────────────────────────────────────────────────────
# Streamed message data classes (lightweight wrappers for streaming chunks)
# ────────────────────────────────────────────────────────────────────

class StreamedFunction:
    """Represents a streamed function call with name and arguments."""
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class StreamedToolCall:
    """Represents a streamed tool call with id, type, and function."""
    def __init__(self, id_val, name, arguments):
        self.id = id_val
        self.type = "function"
        self.function = StreamedFunction(name, arguments)


class StreamedMessage:
    """Represents a fully assembled streamed message with content and tool calls."""
    def __init__(self, content, tool_calls_list):
        self.content = content
        self.tool_calls = tool_calls_list

    def model_dump(self, exclude_none=True):
        res = {"role": "assistant"}
        if self.content:
            res["content"] = self.content
        if self.tool_calls:
            res["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in self.tool_calls
            ]
        return res


# ────────────────────────────────────────────────────────────────────
# Main agent loop
# ────────────────────────────────────────────────────────────────────

def run_agent_loop(ctx):
    """
    Runs the main AI agent loop with streaming, tool dispatch, and retries.

    Args:
        ctx (dict): Mutable context with keys:
            - session_id (int)
            - conversation_history (list[dict])
            - SYSTEM_PROMPT (str)

    Modifies ctx['conversation_history'] in place and persists results to SQLite.
    """
    conversation_history = ctx["conversation_history"]
    current_session_id = ctx["session_id"]

    attempt = 0
    tool_call_count = 0
    loop_iteration = 0
    loop_start_time = time.time()

    # Take a backup snapshot for clean recovery on errors
    safe_history_backup = list(conversation_history)

    while attempt < config.MAX_RETRIES:
        try:
            loop_iteration += 1
            print(f"  [DEBUG] --- Loop iteration {loop_iteration} (attempt={attempt}, tool_calls_so_far={tool_call_count}) ---")

            if attempt > 0:
                print(f"  [Retrying... {attempt}/{config.MAX_RETRIES}]")

            # --- Start timing AI processing ---
            print(f"  [Thinking...] (sending {len(conversation_history)} messages to API)")
            agent_start_time = time.time()

            with OpenRouter(api_key=config.OPENROUTER_API_KEY) as client:
                spinner = Spinner("Reflecting")
                spinner.start()

                full_content = ""
                tool_calls_acc = {}
                first_token_received = False
                last_usage = None

                try:
                    active_tools = get_available_tools(read_only=config.READ_ONLY_MODE)
                    stream_gen = client.chat.send(
                        model=config.MODEL_NAME,
                        messages=conversation_history,
                        tools=active_tools,
                        stream=True
                    )

                    for chunk in stream_gen:
                        # Capture usage from the last chunk
                        chunk_usage = getattr(chunk, "usage", None)
                        if chunk_usage:
                            last_usage = chunk_usage

                        choices = getattr(chunk, "choices", None)
                        if not choices:
                            continue
                        choice = choices[0]
                        delta = getattr(choice, "delta", None)
                        if not delta:
                            continue

                        # Content delta
                        c_delta = getattr(delta, "content", None)
                        if c_delta:
                            if not first_token_received:
                                spinner.stop()
                                first_token_received = True
                                sys.stdout.write("\n  \033[1;35m🤖 Agent\033[0m: ")
                                sys.stdout.flush()
                            sys.stdout.write(c_delta)
                            sys.stdout.flush()
                            full_content += c_delta

                        # Tool calls delta
                        tc_deltas = getattr(delta, "tool_calls", None)
                        if tc_deltas:
                            for tc in tc_deltas:
                                idx = getattr(tc, "index", 0)
                                if idx not in tool_calls_acc:
                                    tool_calls_acc[idx] = {
                                        "id": getattr(tc, "id", "") or f"call_{idx}",
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    }
                                func = getattr(tc, "function", None)
                                if func:
                                    if getattr(func, "name", None):
                                        tool_calls_acc[idx]["function"]["name"] += func.name
                                    if getattr(func, "arguments", None):
                                        tool_calls_acc[idx]["function"]["arguments"] += func.arguments

                finally:
                    spinner.stop()

                agent_end_time = time.time()
                agent_duration = agent_end_time - agent_start_time

                # Record token usage from the stream's last chunk
                tracker = ctx.get("usage_tracker")
                if last_usage and tracker:
                    tracker.record(
                        prompt_tokens=getattr(last_usage, "prompt_tokens", 0),
                        completion_tokens=getattr(last_usage, "completion_tokens", 0),
                        cost=getattr(last_usage, "cost", 0.0)
                    )

                if first_token_received:
                    sys.stdout.write("\n\n")
                    sys.stdout.flush()

                built_tcs = [
                    StreamedToolCall(v["id"], v["function"]["name"], v["function"]["arguments"])
                    for v in tool_calls_acc.values()
                ]
                message = StreamedMessage(full_content, built_tcs)
                print(f"  [DEBUG] API call returned in {agent_duration:.2f}s | has_tool_calls={bool(message.tool_calls)}")

                if hasattr(message, 'tool_calls') and message.tool_calls:
                    if tool_call_count >= config.MAX_TOOL_CALLS:
                        print("  \033[1;31m[System]: Too many tool calls. Forcing stop to prevent infinite loop.\033[0m")
                        ctx["conversation_history"] = safe_history_backup[:-1]
                        break

                    # Colored output for system decisions
                    GREEN = "\033[1;32m"
                    CYAN = "\033[1;36m"
                    RESET = "\033[0m"

                    tool_call_count += len(message.tool_calls)
                    assistant_msg = message.model_dump(exclude_none=True)
                    conversation_history.append(assistant_msg)

                    # Persist the assistant tool-call message to SQLite
                    tc_json = json.dumps(assistant_msg.get("tool_calls", []), ensure_ascii=False)
                    db.save_message(
                        current_session_id, "assistant",
                        assistant_msg.get("content") or "",
                        tool_calls_json=tc_json
                    )

                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        try:
                            args = json.loads(tool_call.function.arguments)
                        except:
                            args = {}

                        # Dynamic Spinner for active Tool Execution
                        args_summary = str(args)[:35] + "..." if len(str(args)) > 35 else str(args)
                        tool_spinner = Spinner(f"Running tool {CYAN}{func_name}{RESET} {args_summary}")
                        tool_spinner.start()

                        try:
                            # Run the dispatcher
                            tool_result = dispatch_tool(func_name, args, read_only=config.READ_ONLY_MODE)

                            # Handle interactive soft-block confirmation prompts
                            if isinstance(tool_result, str) and tool_result.startswith("CONFIRMATION_REQUIRED:"):
                                tool_spinner.stop()

                                RED = "\033[1;31m"
                                confirm_prompt = input(f"\n{RED}[!!!]{RESET} Agent requests to execute dangerous command:\n  '{args.get('command') or args.get('command_line') or func_name}'\nAllow execution? ({GREEN}y{RESET}/{RED}n{RESET}): ").strip().lower()
                                if confirm_prompt == 'y':
                                    args['confirmed'] = True
                                    tool_spinner = Spinner(f"Running tool {CYAN}{func_name}{RESET} {args_summary} (Confirmed)")
                                    tool_spinner.start()
                                    try:
                                        tool_result = dispatch_tool(func_name, args, read_only=config.READ_ONLY_MODE)
                                    finally:
                                        tool_spinner.stop()
                                else:
                                    tool_result = "Error: Command execution declined by the user."
                                    print("  [System]: Command declined by user.")
                        finally:
                            if 'tool_spinner' in locals():
                                try:
                                    tool_spinner.stop()
                                except:
                                    pass

                        # Print success checkmark
                        print(f"  {GREEN}✔{RESET} Executed {CYAN}{func_name}{RESET} successfully.")

                        # Automatically trigger visual diff after file modifications
                        if func_name in {"edit_local_file", "replace_in_file", "delete_local_file", "move_or_rename_file"} and not str(tool_result).startswith("Error"):
                            target_file = args.get("filepath") or args.get("source_path") or args.get("dest_path")
                            diff_utils.show_auto_diff(target_file)

                        tool_msg = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": str(tool_result)
                        }
                        conversation_history.append(tool_msg)
                        # Persist tool result to SQLite
                        db.save_message(
                            current_session_id, "tool",
                            str(tool_result),
                            tool_call_id=tool_call.id,
                            tool_name=func_name
                        )

                    continue

                else:
                    answer = message.content or "[No text response]"
                    total_elapsed = time.time() - loop_start_time
                    print(f"  [DEBUG] Total loop time: {total_elapsed:.2f}s across {loop_iteration} iteration(s)")

                    usage_info = ""
                    if last_usage:
                        prompt_tokens = getattr(last_usage, "prompt_tokens", 0) or 0
                        comp_tokens = getattr(last_usage, "completion_tokens", 0) or 0
                        cost = getattr(last_usage, "cost", 0.0) or 0.0
                        tot_tokens = prompt_tokens + comp_tokens
                        cost_str = f" · ${cost:.4f}" if cost > 0 else ""
                        if tot_tokens > 0:
                            usage_info = f" · {tot_tokens:,} tokens{cost_str}"

                    # Render signature Rich Markdown panel for the agent response
                    print_agent_response(answer, agent_duration, usage_info=usage_info)

                    conversation_history.append({"role": "assistant", "content": answer})
                    db.save_message(current_session_id, "assistant", answer)
                    break

        except KeyboardInterrupt:
            RED = "\033[1;31m"
            RESET = "\033[0m"
            print(f"\n{RED}  [System]: Operation canceled by user (Esc pressed).{RESET}\n")
            ctx["conversation_history"] = list(safe_history_backup)
            break
        except Exception as e:
            attempt += 1
            print(f"  [Error]: {e}")

            # Rollback to safe state on errors
            ctx["conversation_history"] = list(safe_history_backup)
            conversation_history = ctx["conversation_history"]

            if attempt < config.MAX_RETRIES:
                time.sleep(config.RETRY_DELAY)
            else:
                print("  [System]: Max retries reached. Please try asking again.\n")
                ctx["conversation_history"] = conversation_history[:-1]
                break
