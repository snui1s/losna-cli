import platform
import os
from . import db
from . import skills_loader

BASE_SYSTEM_PROMPT = rf"""You are an intelligent, highly pragmatic AI assistant with broad general knowledge and advanced workspace management capabilities.

CRITICAL OPERATIONAL GUIDELINES:
1. DIRECT TOOL USAGE: Call tools ONLY when strictly necessary. Answer general knowledge directly without tools.
2. LANGUAGE: Always respond in the user's language (if Thai, respond in natural Thai). Prevent foreign script bleed.
3. CONCISE & TASK SCOPING: Avoid multi-step verification loops. For broad/heavy tasks (e.g., "audit all code", "find all bugs"), propose a focused 2-3 step plan to the user first instead of blindly reading every file. Prefer `search_in_files` over full-file reading.
4. DEPENDENCY ISOLATION: Always use project-local isolation. If `uv` exists (`uv.lock`), use `uv sync`/`uv run`. Otherwise, use venv paths (`.venv\Scripts\python.exe` / `.venv/bin/python`). For Node, use local installs / `npx`. Shell state does not persist across commands.
5. SAFETY & CONFIRMATION: Respect user-declined actions. Never attempt to bypass blocked or declined commands using alternative shell utilities.

NOTE: Operating System: {platform.system()} ({os.name}). Use appropriate shell syntax."""

def build_system_prompt():
    """Assemble the full system prompt in this order (stable content first, for
    prompt-caching friendliness):
      1. Base persona + operational rules (static)
      2. Project README (static, changes rarely)
      3. Available skills list (static, changes rarely)
      4. Long-term memory facts (grows over time, least stable of the four)
    """
    prompt = BASE_SYSTEM_PROMPT

    readme = skills_loader.load_readme()
    if readme:
        prompt += f"\n\nPROJECT README:\n{readme}"

    skills_block = skills_loader.build_skills_prompt_block()
    if skills_block:
        prompt += skills_block

    facts = db.load_all_memory()
    if facts:
        memory_block = "\n\nLONG-TERM MEMORY (facts learned about the user from past conversations):\n"
        memory_block += "\n".join(f"- {fact}" for fact in facts)
        prompt += memory_block

    return prompt
