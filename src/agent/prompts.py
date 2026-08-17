"""
prompts.py — System prompt builder and OpenRouter prompt caching optimizer.

Constructs structured system prompt payloads with static (persona, README, skills list,
pinned memory) and dynamic (compaction summary, relevant facts, read-only status) components.
"""

import platform
import os
from . import db
from . import skills_loader

BASE_SYSTEM_PROMPT = rf"""You are an intelligent, highly pragmatic AI assistant with broad general knowledge and advanced workspace management capabilities.

CRITICAL OPERATIONAL GUIDELINES:
1. DIRECT TOOL USAGE: Call tools ONLY when strictly necessary. If the project overview or answer is already in your System Prompt (from auto-loaded ai.txt/AGENTS.md, README.md, or skills list), answer the user DIRECTLY without calling `read_skill`, `read_local_file`, or `list_directory` unnecessarily.
2. LANGUAGE: Always respond in the user's language (if Thai, respond in natural Thai). Prevent foreign script bleed.
3. CONCISE & TASK SCOPING: Avoid multi-step verification loops. For broad/heavy tasks (e.g., "audit all code", "find all bugs"), propose a focused 2-3 step plan to the user first instead of blindly reading every file. Prefer `search_in_files` over full-file reading.
4. DEPENDENCY ISOLATION: Always use project-local isolation. If `uv` exists (`uv.lock`), use `uv sync`/`uv run`. Otherwise, use venv paths (`.venv\Scripts\python.exe` / `.venv/bin/python`). For Node, use local installs / `npx`. Shell state does not persist across commands.
5. SAFETY & CONFIRMATION: Respect user-declined actions. Never attempt to bypass blocked or declined commands using alternative shell utilities.

NOTE: Operating System: {platform.system()} ({os.name}). Use appropriate shell syntax."""


AUTO_CONTEXT_FILES = ["ai.txt", "AGENTS.md", "AI.md", ".losnacontext", "CLAUDE.md"]


def load_auto_ai_context():
    """
    Auto-detects and loads project AI context files (e.g. ai.txt, AGENTS.md, AI.md, .losnacontext, CLAUDE.md)
    from current working directory or project root.
    """
    search_dirs = [os.getcwd()]
    try:
        from . import config
        if config.PROJECT_ROOT not in search_dirs:
            search_dirs.append(config.PROJECT_ROOT)
    except Exception:
        pass

    for sdir in search_dirs:
        for fname in AUTO_CONTEXT_FILES:
            fpath = os.path.join(sdir, fname)
            if os.path.isfile(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read(4000).strip()
                    if content:
                        rel_p = os.path.relpath(fpath, os.getcwd()).replace("\\", "/")
                        return fname, rel_p, content
                except Exception:
                    pass
    return None, None, None


def build_system_message(invoked_skill_prompt=None, previous_summary=None, relevant_facts=None, use_cache_control=False, read_only=False):
    """
    Builds system message payload structured for OpenRouter Prompt Caching.
    Static components (Persona, README, Skills List, Pinned Core Memory, Invoked Skill)
    are ordered first to maximize OpenRouter automatic prefix cache hits.
    Optionally applies explicit cache_control blocks for Anthropic/Claude models.

    Args:
        invoked_skill_prompt (str, optional): Instruction content of an invoked skill.
        previous_summary (str, optional): Compacted conversation summary text.
        relevant_facts (list[str], optional): Retrieved dynamic memory facts.
        use_cache_control (bool, optional): Whether to format as dict with ephemeral cache control.
        read_only (bool, optional): Whether Read-Only mode is active.

    Returns:
        dict: OpenRouter system message dictionary.
    """
    static_parts = [BASE_SYSTEM_PROMPT]

    fname, _, ai_context = load_auto_ai_context()
    if ai_context:
        static_parts.append(f"[Auto-Detected Project AI Context ({fname})]:\n{ai_context}")

    readme = skills_loader.load_readme()
    if readme:
        static_parts.append(f"PROJECT README:\n{readme}")

    skills_block = skills_loader.build_skills_prompt_block()
    if skills_block:
        static_parts.append(skills_block.strip())

    pinned_facts = db.load_pinned_memory()
    if pinned_facts:
        pinned_block = "[Core Memory / Pinned Facts]:\n" + "\n".join(f"- {f}" for f in pinned_facts)
        static_parts.append(pinned_block)

    if invoked_skill_prompt:
        static_parts.append(invoked_skill_prompt.strip())

    static_text = "\n\n".join(p for p in static_parts if p)

    dynamic_parts = []
    if read_only:
        dynamic_parts.append(
            "[READ-ONLY MODE ACTIVE]: You are operating in Read-Only Mode. "
            "You CANNOT edit/modify files, delete files, or execute shell commands. "
            "Limit all operations strictly to reading, searching, inspecting, and answering questions."
        )

    if previous_summary:
        dynamic_parts.append(f"[Previous Context Summary]: {previous_summary}")

    if relevant_facts:
        facts_block = "[Relevant Dynamic Facts]:\n" + "\n".join(f"- {f}" for f in relevant_facts)
        dynamic_parts.append(facts_block)

    dynamic_text = "\n\n".join(p for p in dynamic_parts if p)

    if use_cache_control:
        content = [
            {
                "type": "text",
                "text": static_text,
                "cache_control": {"type": "ephemeral"}
            }
        ]
        if dynamic_text:
            content.append({
                "type": "text",
                "text": dynamic_text
            })
        return {"role": "system", "content": content}
    else:
        full_text = f"{static_text}\n\n{dynamic_text}".strip() if dynamic_text else static_text
        return {"role": "system", "content": full_text}


def build_system_prompt(invoked_skill_prompt=None, previous_summary=None, relevant_facts=None, read_only=False):
    """
    Backward-compatible helper returning plain system prompt string.

    Args:
        invoked_skill_prompt (str, optional): Instruction content of an invoked skill.
        previous_summary (str, optional): Compacted conversation summary text.
        relevant_facts (list[str], optional): Retrieved dynamic memory facts.
        read_only (bool, optional): Whether Read-Only mode is active.

    Returns:
        str: Plain text system prompt.
    """
    msg = build_system_message(
        invoked_skill_prompt=invoked_skill_prompt,
        previous_summary=previous_summary,
        relevant_facts=relevant_facts,
        use_cache_control=False,
        read_only=read_only
    )
    return msg["content"]
