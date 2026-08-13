import os
import re
from .tools import truncate_content

# Regex to match @filepath tokens in prompt text (e.g. @src/agent/main.py or @hello.txt)
MENTION_PATTERN = re.compile(r"@([a-zA-Z0-9_\-\.\/\\]+)")


def extract_file_mentions(text: str):
    """
    Scans input text for @filepath candidates and returns a list of existing valid file paths.
    """
    if not text or "@" not in text:
        return []

    candidates = MENTION_PATTERN.findall(text)
    valid_paths = []
    base_dir = os.path.realpath(os.getcwd())

    for raw_path in candidates:
        # Clean trailing punctuation if user typed "@hello.txt," or "@hello.txt."
        clean_path = raw_path.rstrip(".,;:!?")
        if not clean_path:
            continue

        target_path = os.path.realpath(clean_path)

        # Security check: must reside inside project working directory
        if not target_path.startswith(base_dir):
            continue

        if os.path.isfile(target_path) and clean_path not in valid_paths:
            valid_paths.append(clean_path)

    return valid_paths


def load_file_attachments(filepaths):
    """
    Reads content from list of valid file paths.
    Truncates content if file is too large to prevent token overflow.
    """
    attachments = []
    for rel_path in filepaths:
        try:
            with open(rel_path, "r", encoding="utf-8", errors="replace") as f:
                raw_content = f.read()

            truncated = truncate_content(raw_content, max_chars=8000)
            attachments.append({
                "path": rel_path,
                "content": truncated
            })
        except Exception as e:
            attachments.append({
                "path": rel_path,
                "content": f"Error reading file: {str(e)}"
            })

    return attachments


def build_mention_prompt_block(attachments):
    """
    Formats list of file attachments into a clean system instruction payload.
    """
    if not attachments:
        return ""

    blocks = ["[Attached File Context from @mentions]:"]
    for att in attachments:
        blocks.append(f"\n--- File: {att['path']} ---\n{att['content']}")

    return "\n".join(blocks)
