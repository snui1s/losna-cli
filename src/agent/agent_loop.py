"""
agent_loop.py — OpenRouter streaming API loop with tool dispatch for Losna CLI.

Handles the core AI conversation loop: streaming responses, accumulating tool calls,
executing tools with confirmation dialogs, and persisting results to SQLite.
"""

import os
import sys
import time
import json
import threading
from openrouter import OpenRouter
from . import config
from . import db
from . import diff_utils
from .tools import dispatch_tool, get_available_tools
from .ui import Spinner, StreamBorderRenderer
from .diagnostics import check_openrouter_health, format_diagnostic_summary


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
    effective_max_tools = config.MAX_TOOL_CALLS
    force_synthesis = False
    loop_iteration = 0
    loop_start_time = time.time()

    # Take a backup snapshot for clean recovery on errors
    safe_history_backup = list(conversation_history)

    while attempt < config.MAX_RETRIES:
        try:
            loop_iteration += 1
            if getattr(config, "DEBUG", False):
                print(f"  [DEBUG] --- Loop iteration {loop_iteration} (attempt={attempt}, tool_calls_so_far={tool_call_count}) ---")

            if attempt > 0:
                print(f"  [Retrying... {attempt}/{config.MAX_RETRIES}]")

            # --- Start timing AI processing ---
            if getattr(config, "DEBUG", False):
                print(f"  [Thinking...] (sending {len(conversation_history)} messages to API)")
            agent_start_time = time.time()

            with OpenRouter(api_key=config.OPENROUTER_API_KEY) as client:
                spinner = Spinner("Reflecting", show_timer=True, auto_status=True)
                spinner.start()

                full_content = ""
                tool_calls_acc = {}
                first_token_received = False
                last_usage = None
                renderer = StreamBorderRenderer()

                # Background health watcher: check OpenRouter connectivity if TTFT exceeds 20 seconds
                health_stop_evt = threading.Event()

                def _bg_health_watcher():
                    if not health_stop_evt.wait(20.0):
                        if not first_token_received and not spinner.stop_event.is_set():
                            diag = check_openrouter_health(config.OPENROUTER_API_KEY, timeout=3.5)
                            if not first_token_received and not spinner.stop_event.is_set():
                                status = diag.get("status")
                                if status == "OK":
                                    latency = diag.get("latency_ms", 0)
                                    spinner.set_diagnostic_tag(f"\033[1;32m[OpenRouter OK ({latency}ms)]\033[0m")
                                elif status == "AUTH_ERROR":
                                    spinner.set_diagnostic_tag("\033[1;31m[OpenRouter Auth Error]\033[0m")
                                elif status == "RATE_LIMITED":
                                    spinner.set_diagnostic_tag("\033[1;33m[OpenRouter Rate Limited]\033[0m")
                                elif status == "GATEWAY_ERROR":
                                    spinner.set_diagnostic_tag("\033[1;31m[OpenRouter Gateway 5xx]\033[0m")
                                else:
                                    spinner.set_diagnostic_tag("\033[1;31m[OpenRouter Unreachable]\033[0m")

                health_thread = threading.Thread(target=_bg_health_watcher, daemon=True)
                health_thread.start()

                try:
                    import re
                    has_thai = any(
                        bool(re.search(r'[\u0e00-\u0e7f]', str(m.get("content", ""))))
                        for m in conversation_history if m.get("role") == "user"
                    )

                    payload_messages = list(conversation_history)
                    if has_thai and payload_messages and payload_messages[0].get("role") == "system":
                        sys_content = payload_messages[0].get("content")
                        if isinstance(sys_content, str) and "[STRICT THAI LANGUAGE ENFORCEMENT]" not in sys_content:
                            payload_messages[0] = {
                                **payload_messages[0],
                                "content": sys_content + "\n\n[STRICT THAI LANGUAGE ENFORCEMENT: The user is writing in Thai (ภาษาไทย). You MUST answer 100% in natural Thai. Absolutely NEVER output any Chinese characters (中文 / 汉字) or other foreign languages.]"
                            }

                    if force_synthesis:
                        payload_messages.append({
                            "role": "system",
                            "content": "[System Note]: Tool call limit reached. Please provide a direct, comprehensive final answer based on the findings and tool outputs gathered above without making any further tool calls."
                        })
                        active_tools = None
                    else:
                        active_tools = get_available_tools(read_only=config.READ_ONLY_MODE)

                    stream_gen = client.chat.send(
                        model=config.MODEL_NAME,
                        messages=payload_messages,
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
                                health_stop_evt.set()
                                spinner.stop()
                                first_token_received = True
                            renderer.on_token(c_delta)
                            full_content += c_delta

                        # Tool calls delta
                        tc_deltas = getattr(delta, "tool_calls", None)
                        if tc_deltas:
                            if not first_token_received:
                                health_stop_evt.set()
                                spinner.stop()
                                first_token_received = True
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
                    health_stop_evt.set()
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

                built_tcs = [
                    StreamedToolCall(v["id"], v["function"]["name"], v["function"]["arguments"])
                    for v in tool_calls_acc.values()
                ]
                message = StreamedMessage(full_content, built_tcs)
                if getattr(config, "DEBUG", False):
                    print(f"  [DEBUG] API call returned in {agent_duration:.2f}s | has_tool_calls={bool(message.tool_calls)}")

                if hasattr(message, 'tool_calls') and message.tool_calls:
                    if first_token_received:
                        renderer.finish_intermediate()

                    if (tool_call_count + len(message.tool_calls) > effective_max_tools) or (tool_call_count >= effective_max_tools):
                        YELLOW = "\033[1;33m"
                        GREEN = "\033[1;32m"
                        CYAN = "\033[1;36m"
                        RED = "\033[1;31m"
                        RESET = "\033[0m"

                        is_interactive = sys.stdin.isatty() and not os.environ.get("PYTEST_CURRENT_TEST")
                        choice = "c"

                        if is_interactive:
                            total_requested = tool_call_count + len(message.tool_calls)
                            print(f"\n{YELLOW}[!] Tool Call Limit Reached ({total_requested}/{effective_max_tools} calls in this turn){RESET}")
                            print(f"  {GREEN}[c] Continue{RESET}  - Grant +{config.MAX_TOOL_CALLS} more tool calls and continue")
                            print(f"  {CYAN}[s] Summarize{RESET} - Stop calling tools and synthesize answer from data gathered so far")
                            print(f"  {RED}[a] Abort{RESET}     - Cancel and revert this turn")
                            try:
                                user_choice = input(f"Select option ({GREEN}c{RESET}/{CYAN}s{RESET}/{RED}a{RESET}, default: {GREEN}c{RESET}): ").strip().lower()
                                if user_choice:
                                    choice = user_choice
                            except (EOFError, KeyboardInterrupt):
                                choice = "a"
                        else:
                            choice = "s"

                        if choice in ("c", "continue", "y", "yes"):
                            effective_max_tools += max(config.MAX_TOOL_CALLS, len(message.tool_calls))
                            print(f"  {GREEN}✔ Extended tool limit to {effective_max_tools} calls for this turn.{RESET}\n")
                        elif choice in ("s", "summarize", "stop", "answer"):
                            print(f"  {CYAN}ℹ Synthesizing final response from gathered results...{RESET}\n")
                            force_synthesis = True
                            assistant_msg = message.model_dump(exclude_none=True)
                            conversation_history.append(assistant_msg)
                            tc_json = json.dumps(assistant_msg.get("tool_calls", []), ensure_ascii=False)
                            db.save_message(
                                current_session_id, "assistant",
                                assistant_msg.get("content") or "",
                                tool_calls_json=tc_json
                            )
                            for tc in message.tool_calls:
                                note = "Tool execution stopped by user. Please synthesize the final response based on all data gathered so far."
                                conversation_history.append({
                                    "role": "tool",
                                    "tool_call_id": tc.id,
                                    "name": tc.function.name,
                                    "content": note
                                })
                                db.save_message(
                                    current_session_id, "tool",
                                    note,
                                    tool_call_id=tc.id,
                                    tool_name=tc.function.name
                                )
                            continue
                        else:
                            print(f"  {RED}[System]: Operation aborted by user. Reverting to previous state.{RESET}\n")
                            ctx["conversation_history"] = list(safe_history_backup)
                            break

                    # Colored output for system decisions
                    GREEN = "\033[1;32m"
                    CYAN = "\033[1;36m"
                    RED = "\033[1;31m"
                    RESET = "\033[0m"

                    tool_call_count += len(message.tool_calls)
                    assistant_msg = message.model_dump(exclude_none=True)
                    conversation_history.append(assistant_msg)

                    tc_json = json.dumps(assistant_msg.get("tool_calls", []), ensure_ascii=False)
                    saved_assistant_in_db = False

                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        try:
                            args = json.loads(tool_call.function.arguments)
                        except (json.JSONDecodeError, TypeError):
                            args = {}

                        # Dynamic Spinner for active Tool Execution
                        args_summary = str(args)[:35] + "..." if len(str(args)) > 35 else str(args)
                        tool_spinner = Spinner(f"Running tool {CYAN}{func_name}{RESET} {args_summary}")
                        tool_spinner.start()

                        try:
                            # Run the dispatcher (user_confirmed=False ensures initial check)
                            tool_result = dispatch_tool(func_name, args, read_only=config.READ_ONLY_MODE, user_confirmed=False)

                            # Handle interactive soft-block confirmation prompts
                            if isinstance(tool_result, str) and tool_result.startswith("CONFIRMATION_REQUIRED:"):
                                tool_spinner.stop()

                                confirm_prompt = input(f"\n{RED}[!!!]{RESET} Agent requests to execute dangerous command:\n  '{args.get('command') or args.get('command_line') or func_name}'\nAllow execution? ({GREEN}y{RESET}/{RED}n{RESET}): ").strip().lower()
                                if confirm_prompt == 'y':
                                    tool_spinner = Spinner(f"Running tool {CYAN}{func_name}{RESET} {args_summary} (Confirmed)")
                                    tool_spinner.start()
                                    try:
                                        tool_result = dispatch_tool(func_name, args, read_only=config.READ_ONLY_MODE, user_confirmed=True)
                                    finally:
                                        tool_spinner.stop()
                                else:
                                    tool_result = "Error: Command execution declined by the user."
                                    print("  [System]: Command declined by user.")
                        finally:
                            tool_spinner.stop()

                        # Print success checkmark only on actual success
                        if not str(tool_result).startswith("Error"):
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

                        # Save assistant_msg to SQLite on first successful tool call
                        if not saved_assistant_in_db:
                            db.save_message(
                                current_session_id, "assistant",
                                assistant_msg.get("content") or "",
                                tool_calls_json=tc_json
                            )
                            saved_assistant_in_db = True

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
                    if getattr(config, "DEBUG", False):
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

                    if first_token_received:
                        renderer.finish(agent_duration, usage_info)
                    else:
                        renderer.render_fallback(answer, agent_duration, usage_info)

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

            # Run diagnostic check to give actionable insights to the user
            try:
                diag = check_openrouter_health(config.OPENROUTER_API_KEY, timeout=3.5)
                diag_summary = format_diagnostic_summary(diag, config.MODEL_NAME)
                print(diag_summary)
            except Exception:
                pass

            # Rollback to safe state on errors
            ctx["conversation_history"] = list(safe_history_backup)
            conversation_history = ctx["conversation_history"]

            if attempt < config.MAX_RETRIES:
                time.sleep(config.RETRY_DELAY)
            else:
                print("  [System]: Max retries reached. Please try asking again.\n")
                ctx["conversation_history"] = conversation_history[:-1]
                break
