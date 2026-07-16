import os

# Resolve script directory for absolute path references
script_dir = os.path.dirname(os.path.abspath(__file__))
# C:\random\openrouter\src\agent -> C:\random\openrouter
PROJECT_ROOT = os.path.abspath(os.path.join(script_dir, "..", ".."))

# Load environment variables from local .env file relative to script location
env_path = os.path.join(PROJECT_ROOT, ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# --- Configurations ---
#MODEL_NAME = "google/gemma-4-31b-it"
MODEL_NAME = "deepseek/deepseek-v4-flash"
COMPACTION_MODEL = "google/gemini-2.5-flash-lite"

MAX_RETRIES = 3
RETRY_DELAY = 2

# Memory management parameters
MAX_ACTIVE_MESSAGES = 25
KEEP_RECENT = 4
MAX_TOOL_CALLS = 25

# API Keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
