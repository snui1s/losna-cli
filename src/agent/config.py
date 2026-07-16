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
    except:
        pass

def get_or_prompt_key(env_name: str, display_name: str) -> str:
    """Retrieve key from global config ~/.losnarc, or prompt user interactively."""
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

# --- Configurations ---
MODEL_NAME = "deepseek/deepseek-v4-flash"
COMPACTION_MODEL = "google/gemini-2.5-flash-lite"

MAX_RETRIES = 3
RETRY_DELAY = 2

# Memory management parameters
MAX_ACTIVE_MESSAGES = 25
KEEP_RECENT = 4
MAX_TOOL_CALLS = 25

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
    except:
        pass
