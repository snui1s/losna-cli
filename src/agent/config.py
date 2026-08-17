"""
config.py — Global configuration and key management module.

Handles resolving project paths, loading/persisting settings in ~/.losnarc,
prompting for required API keys, and managing runtime model parameters.
"""

import os
import json
from pathlib import Path

# Resolve script directory for absolute path references
script_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(script_dir, "..", ".."))


# Check global ~/.losnarc for keys
home_config_path = Path.home() / ".losnarc"
global_config = {}
if home_config_path.exists():
    try:
        with open(home_config_path, "r", encoding="utf-8") as f:
            global_config = json.load(f)
    except Exception:
        pass


def get_or_prompt_key(env_name: str, display_name: str) -> str:
    """
    Retrieves key from global config ~/.losnarc, or prompts user interactively.

    Args:
        env_name (str): Configuration key name in ~/.losnarc.
        display_name (str): Human-readable name for terminal prompt.

    Returns:
        str: The retrieved or entered API key string.
    """
    val = global_config.get(env_name)
    if val:
        return val

    print(f"\n\033[1;33m[Losna Config]:\033[0m {display_name} not found.")
    user_val = input(f"Please enter your {display_name}: ").strip()

    global_config[env_name] = user_val
    try:
        with open(home_config_path, "w", encoding="utf-8") as f:
            json.dump(global_config, f, indent=4)
        print(f"\033[1;32mSaved globally to {home_config_path}\033[0m")
    except Exception as e:
        print(f"\033[1;31mFailed to save config globally: {e}\033[0m")

    return user_val


def save_global_config():
    """Helper function to save global_config dictionary to ~/.losnarc."""
    try:
        with open(home_config_path, "w", encoding="utf-8") as f:
            json.dump(global_config, f, indent=4)
    except Exception as e:
        print(f"\033[1;31mFailed to save config globally: {e}\033[0m")


# --- Configurations ---
try:
    import importlib.metadata
    VERSION = importlib.metadata.version("losna-cli")
except Exception:
    VERSION = "0.3.0"

MODEL_NAME = global_config.get("MODEL_NAME", "deepseek/deepseek-v4-flash")
COMPACTION_MODEL = "google/gemini-2.5-flash-lite"
READ_ONLY_MODE = global_config.get("READ_ONLY_MODE", False)
ENTER_2_CONFIRM = global_config.get("ENTER_2_CONFIRM", False)


def set_read_only_mode(enabled: bool):
    """
    Toggles the Read-Only Mode setting and persists to ~/.losnarc.

    Args:
        enabled (bool): True to enable Read-Only Mode, False to disable.
    """
    global READ_ONLY_MODE
    READ_ONLY_MODE = enabled
    global_config["READ_ONLY_MODE"] = enabled
    save_global_config()


def set_enter_2_confirm(enabled: bool):
    """
    Toggles the Double-Enter Confirmation setting and persists to ~/.losnarc.

    Args:
        enabled (bool): True to require pressing Enter twice to send prompts, False to disable.
    """
    global ENTER_2_CONFIRM
    ENTER_2_CONFIRM = enabled
    global_config["ENTER_2_CONFIRM"] = enabled
    save_global_config()


def update_model_name(new_model_name: str):
    """
    Saves the selected OpenRouter model globally in ~/.losnarc.

    Args:
        new_model_name (str): The OpenRouter model ID string (e.g. 'google/gemini-2.5-pro').
    """
    global MODEL_NAME
    MODEL_NAME = new_model_name
    global_config["MODEL_NAME"] = new_model_name
    try:
        with open(home_config_path, "w", encoding="utf-8") as f:
            json.dump(global_config, f, indent=4)
        print(f"\033[1;32mModel updated globally to: {new_model_name}\033[0m")
    except Exception as e:
        print(f"\033[1;31mFailed to save new model globally: {e}\033[0m")


MAX_RETRIES = 3
RETRY_DELAY = 2

# Memory management parameters
MAX_ACTIVE_MESSAGES = 25
KEEP_RECENT = 4
MAX_TOOL_CALLS = global_config.get("MAX_TOOL_CALLS", 25)


def set_max_tool_calls(limit: int):
    """
    Sets the MAX_TOOL_CALLS limit per turn and persists to ~/.losnarc.

    Args:
        limit (int): Maximum number of tool calls allowed per turn.
    """
    global MAX_TOOL_CALLS
    MAX_TOOL_CALLS = limit
    global_config["MAX_TOOL_CALLS"] = limit
    save_global_config()


DISABLED_SKILLS = set(s.lower() for s in global_config.get("DISABLED_SKILLS", []))


def is_skill_disabled(skill_name: str) -> bool:
    """Check if a skill is disabled globally."""
    return skill_name.lower() in DISABLED_SKILLS


def disable_skill(skill_name: str):
    """Disables a skill globally and persists to ~/.losnarc."""
    global DISABLED_SKILLS
    DISABLED_SKILLS.add(skill_name.lower())
    global_config["DISABLED_SKILLS"] = sorted(list(DISABLED_SKILLS))
    save_global_config()


def enable_skill(skill_name: str):
    """Enables a skill globally and persists to ~/.losnarc."""
    global DISABLED_SKILLS
    DISABLED_SKILLS.discard(skill_name.lower())
    global_config["DISABLED_SKILLS"] = sorted(list(DISABLED_SKILLS))
    save_global_config()


# Dynamically resolve keys
# OpenRouter is required, so we prompt if missing
OPENROUTER_API_KEY = get_or_prompt_key("OPENROUTER_API_KEY", "OpenRouter API Key")

# Resolve Tavily key dynamically
TAVILY_API_KEY = global_config.get("TAVILY_API_KEY")
# If not saved, ask if they want to enable the web search feature
if TAVILY_API_KEY is None and "TAVILY_ENABLED" not in global_config:
    print(f"\n\033[1;33m[Losna Config]:\033[0m Do you want to enable the Web Search feature? (y/n)")
    ans = input("Answer (default: n): ").strip().lower()
    if ans == 'y':
        TAVILY_API_KEY = get_or_prompt_key("TAVILY_API_KEY", "Tavily API Key")
        global_config["TAVILY_ENABLED"] = True
    else:
        global_config["TAVILY_ENABLED"] = False
        TAVILY_API_KEY = ""
    # Save selection state
    try:
        with open(home_config_path, "w", encoding="utf-8") as f:
            json.dump(global_config, f, indent=4)
    except Exception:
        pass
