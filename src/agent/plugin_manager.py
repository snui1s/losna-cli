"""
plugin_manager.py — Remote skill plugin management module.

Handles cloning remote Git repositories into temporary storage, extracting SKILL.md
package directories, and installing or removing skill plugins in the project workspace.
"""

import os
import shutil
import tempfile
import subprocess
from . import skills_loader


def install_plugin(repo_url: str, skill_name: str = None) -> str:
    """
    Clones a remote Git repository to a temporary folder, filters for the specified
    skill directory (or searches for any valid SKILL.md folder), and copies it
    into the project's local 'skills/' directory.

    Args:
        repo_url (str): The URL to the Git repository (e.g. 'https://github.com/vercel-labs/agent-skills')
        skill_name (str, optional): Specific skill folder name to extract. If not provided,
                                    scans and copies all valid skill folders.

    Returns:
        str: A status message indicating success or failure.
    """
    # Clean Git URL (remove trailing slashes, ensure correct scheme)
    repo_url = repo_url.strip()

    temp_dir = tempfile.mkdtemp()
    try:
        print(f"  [Plugin Manager]: Cloning repository from '{repo_url}'...")
        # Use git clone --depth 1 for fast network performance
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode != 0:
            return f"Error: Git clone failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

        # Resolve destination path (project-local 'skills/')
        project_root = skills_loader._project_root()
        dest_skills_dir = os.path.join(project_root, "skills")
        os.makedirs(dest_skills_dir, exist_ok=True)

        # Scan cloned repo for skill packages
        installed_skills = []

        # Scenario A: User specified a particular skill folder name
        if skill_name:
            skill_name = skill_name.strip()
            candidates = [
                os.path.join(temp_dir, "skills", skill_name),
                os.path.join(temp_dir, skill_name)
            ]

            selected_src = None
            for cand in candidates:
                if os.path.isdir(cand) and os.path.isfile(os.path.join(cand, "SKILL.md")):
                    selected_src = cand
                    break

            if not selected_src:
                return f"Error: Could not find skill '{skill_name}' containing a 'SKILL.md' in the cloned repository."

            dest_folder = os.path.join(dest_skills_dir, skill_name)
            if os.path.exists(dest_folder):
                shutil.rmtree(dest_folder)
            shutil.copytree(selected_src, dest_folder)
            installed_skills.append(skill_name)

        # Scenario B: Auto-detect all valid skills in the cloned repo
        else:
            found_skills = []
            for root, dirs, files in os.walk(temp_dir):
                if ".git" in root or ".venv" in root:
                    continue
                if "SKILL.md" in files:
                    found_skills.append(root)

            if not found_skills:
                return "Error: No valid skills (directories containing 'SKILL.md') found in the repository."

            for src_dir in found_skills:
                dir_name = os.path.basename(src_dir)
                if dir_name.lower() == "skills" or not dir_name:
                    continue

                dest_folder = os.path.join(dest_skills_dir, dir_name)
                if os.path.exists(dest_folder):
                    shutil.rmtree(dest_folder)
                shutil.copytree(src_dir, dest_folder)
                installed_skills.append(dir_name)

        if not installed_skills:
            return "Error: No skills were copied."

        success_msg = f"Success! Installed {len(installed_skills)} skill(s):\n"
        for s in installed_skills:
            success_msg += f"  - /{s}\n"
        success_msg += "\nType '/help' to see updated command suggestions."
        return success_msg

    except Exception as e:
        return f"Error installing plugin: {str(e)}"
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


def remove_plugin(skill_name: str) -> str:
    """
    Deletes the specified skill plugin folder from the project's local 'skills/' directory.

    Args:
        skill_name (str): The name of the skill/folder to remove (e.g. 'caveman').

    Returns:
        str: Status message indicating success or failure.
    """
    skill_name = skill_name.strip().lower()
    if not skill_name:
        return "Error: No skill name provided."

    if "/" in skill_name or "\\" in skill_name or ".." in skill_name:
        return "Error: Invalid skill name (path traversal not allowed)."

    project_root = skills_loader._project_root()
    skill_dir = os.path.join(project_root, "skills", skill_name)

    if not os.path.isdir(skill_dir):
        return f"Error: Skill '{skill_name}' is not installed."

    try:
        shutil.rmtree(skill_dir)
        return f"Success! Removed plugin/skill '/{skill_name}' from your project."
    except Exception as e:
        return f"Error removing plugin '{skill_name}': {str(e)}"
