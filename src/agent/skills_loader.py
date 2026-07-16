"""
skills_loader.py - Loads project context for the system prompt.

Two layers:
1. README.md at project root - loaded IN FULL, always, as static context.
2. skills/<name>/SKILL.md - only the short description is loaded upfront (cheap).
   The full content is loaded on demand via read_skill(), when the agent decides
   a task actually needs it - keeps the system prompt lean instead of dumping
   every .md file into every request.

This mirrors the "skills" pattern: a directory of specialized docs, each with
a lightweight description that lets the agent decide what to pull in, rather
than the agent (or us) trying to guess relevance via keyword matching.
"""

import os

README_MAX_CHARS = 20000   # cap so one giant README can't blow up every prompt
SKILL_MAX_CHARS = 20000    # cap for a single skill's full content when loaded


def _project_root():
    return os.path.realpath(os.getcwd())


def load_readme():
    """
    Read README.md at the project root in full, if it exists.
    Returns "" if there's no README - callers should just skip the block then.
    """
    root = _project_root()
    readme_path = os.path.join(root, "README.md")

    if not os.path.exists(readme_path):
        return ""

    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"  [Skills]: Could not read README.md ({e})")
        return ""

    if len(content) > README_MAX_CHARS:
        content = content[:README_MAX_CHARS] + "\n\n[...README truncated, too long to include in full...]"

    return content


def _extract_description(content, skill_name):
    """
    Pull a one-line description out of a SKILL.md file's content.
    Looks for a line starting with 'Description:' first; falls back to the
    first non-empty, non-heading line; falls back to the skill's folder name.
    """
    lines = content.splitlines()

    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("description:"):
            return stripped[len("description:"):].strip()

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            return stripped[:200]

    return f"(no description provided for '{skill_name}')"


def list_skills():
    """
    Scan skills/<name>/SKILL.md for every skill in the project.
    Returns a list of dicts: {"name": ..., "description": ..., "path": ...}
    Only reads descriptions here - NOT full content, to keep this cheap to
    call on every session start.
    """
    root = _project_root()
    skills_dir = os.path.join(root, "skills")

    if not os.path.isdir(skills_dir):
        return []

    results = []
    try:
        for entry in sorted(os.listdir(skills_dir)):
            skill_folder = os.path.join(skills_dir, entry)
            skill_file = os.path.join(skill_folder, "SKILL.md")

            if not os.path.isdir(skill_folder) or not os.path.isfile(skill_file):
                continue

            try:
                with open(skill_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"  [Skills]: Could not read {skill_file} ({e})")
                continue

            description = _extract_description(content, entry)
            results.append({
                "name": entry,
                "description": description,
                "path": os.path.join("skills", entry, "SKILL.md")
            })
    except Exception as e:
        print(f"  [Skills]: Could not scan skills directory ({e})")
        return []

    return results


def build_skills_prompt_block():
    """
    Format the skills list for inclusion in the system prompt - just names
    and descriptions, so the agent knows what's available and can call
    read_skill(name) if a task actually needs one.
    """
    skills = list_skills()
    if not skills:
        return ""

    lines = [
        "\n\nAVAILABLE SKILLS (call the 'read_skill' tool to load full details when a task needs one):",
    ]
    for s in skills:
        lines.append(f"- {s['name']}: {s['description']}")
    lines.append(
        "\nIf a task matches MORE THAN ONE skill (e.g. a security review that also "
        "requires careful code reading), call 'read_skill' for every relevant skill "
        "before starting the task - you can pass multiple skill names at once as a "
        "comma-separated list (e.g. skill_name='security-review,code-navigation') "
        "instead of calling the tool once per skill."
    )
    return "\n".join(lines)


def read_skill(skill_name):
    """
    Tool function: load the full content of one or more skills' SKILL.md on demand.
    Accepts either a single skill name, or multiple names separated by commas
    (e.g. "security-review,code-navigation") to load several at once in one call.
    Security: each name must be a plain folder name, no path traversal.
    """
    if not skill_name or not skill_name.strip():
        return "Error: No skill name provided."

    names = [n.strip() for n in skill_name.split(",") if n.strip()]
    if not names:
        return "Error: No valid skill name provided."

    root = _project_root()
    skills_dir = os.path.realpath(os.path.join(root, "skills"))

    results = []
    for name in names:
        if "/" in name or "\\" in name or ".." in name:
            results.append(f"Error: Invalid skill name '{name}'.")
            continue

        skill_file = os.path.realpath(os.path.join(root, "skills", name, "SKILL.md"))

        # Guard against path traversal / symlink tricks, same pattern as tools.py
        if os.path.commonpath([skills_dir, skill_file]) != skills_dir:
            results.append(f"Error: Security block! Invalid skill path for '{name}'.")
            continue

        if not os.path.isfile(skill_file):
            results.append(f"Error: Skill '{name}' not found. Use one of the listed skill names.")
            continue

        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            results.append(f"Error reading skill '{name}': {str(e)}")
            continue

        if len(content) > SKILL_MAX_CHARS:
            content = content[:SKILL_MAX_CHARS] + "\n\n[...skill content truncated...]"

        results.append(f"Content of skill '{name}':\n{content}")

    return "\n\n---\n\n".join(results)