import os
import time
import json
from openrouter import OpenRouter
from . import db

def _extract_json_array(text):
    """
    Extract raw JSON array substring between '[' and ']' from LLM output,
    stripping markdown fences and extraneous leading/trailing text.
    """
    if not text:
        return ""
    cleaned = text.strip()
    if "```" in cleaned:
        lines = cleaned.splitlines()
        filtered = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(filtered).strip()

    start_idx = cleaned.find("[")
    end_idx = cleaned.rfind("]")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return cleaned[start_idx : end_idx + 1]
    return cleaned


def _parse_compaction_response(raw_text):
    """
    Split a combined 'SUMMARY: ... FACTS: [...]' response into (summary, facts).
    FACTS is expected to be a JSON array of objects:
    [
        {"action": "ADD", "text": "...", "is_pinned": false},
        {"action": "SUPERSEDE", "old": "...", "text": "...", "is_pinned": false},
        {"action": "SKIP", "text": "..."}
    ]
    Also supports fallback list of strings if model returns plain string array.
    """
    summary = raw_text.strip()
    facts = []

    if "FACTS:" in raw_text:
        summary_part, facts_part = raw_text.split("FACTS:", 1)
        summary_part = summary_part.strip()
        if summary_part.upper().startswith("SUMMARY:"):
            summary_part = summary_part[len("SUMMARY:"):].strip()
        summary = summary_part or summary

        json_str = _extract_json_array(facts_part)
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        facts.append(item)
                    elif isinstance(item, str) and item.strip():
                        facts.append({"action": "ADD", "text": item.strip()})
        except Exception:
            print("  [Warning]: Could not parse FACTS JSON from LLM response.")
            facts = []
    elif raw_text.strip().upper().startswith("SUMMARY:"):
        summary = raw_text.strip()[len("SUMMARY:"):].strip()

    return summary, facts


def compact_memory(conversation_history, max_active_messages, keep_recent, model_name, system_prompt, session_id=None):
    """
    Function: Triggers memory compaction if active history exceeds max_active_messages.
    Extracts durable facts with structured LLM decisions (ADD, SUPERSEDE, SKIP, is_pinned)
    and updates SQLite long-term memory.

    Returns:
        list: The updated conversation history (compacted or not).
    """
    if len(conversation_history) > max_active_messages:
        print("\n  [System]: Memory full. Triggering Compaction...")
        
        messages_to_compact = conversation_history[:-keep_recent] if keep_recent > 0 else conversation_history
        recent_messages = conversation_history[-keep_recent:] if keep_recent > 0 else []
        
        db.archive_messages(session_id, messages_to_compact)
        print(f"  [Storage]: Archived {len(messages_to_compact)} messages.")

        newly_archived_count = sum(1 for m in messages_to_compact if m.get("role") != "system")
        
        # Fetch existing facts from DB to provide to LLM for deduplication and supersede checks
        existing_facts = db.get_all_fact_texts()
        existing_facts_block = "\n".join(f"- {f}" for f in existing_facts) if existing_facts else "None"

        combined_prompt = (
            "You are compacting a conversation history into durable facts.\n\n"
            f"--- EXISTING FACTS IN MEMORY DATABASE ---\n{existing_facts_block}\n\n"
            "Read the messages below and respond in EXACTLY this format:\n\n"
            "SUMMARY: <a concise summary of the key context from these messages>\n"
            "FACTS: <a JSON array of objects with keys:\n"
            "  - \"action\": \"ADD\" | \"SUPERSEDE\" | \"SKIP\"\n"
            "  - \"text\": \"<new or updated fact sentence>\"\n"
            "  - \"old\": \"<exact text of old fact being replaced>\" (ONLY required if action is \"SUPERSEDE\")\n"
            "  - \"is_pinned\": true | false (Set true ONLY for core identity e.g. user name, primary language preference, medical/allergy safety, or critical rules; false for general facts)\n"
            ">\n\n"
            "Rules for FACTS:\n"
            "1. ADD: New durable fact not covered by existing facts.\n"
            "2. SUPERSEDE: New fact updates, replaces, or contradicts an existing fact.\n"
            "3. SKIP: Fact is already fully covered in EXISTING FACTS.\n\n"
            "Messages to compact:\n"
        )
        for msg in messages_to_compact:
            combined_prompt += f"{msg['role'].upper()}: {msg.get('content') or ''}\n"
            
        try:
            print("  [System]: Compacting context (summarizing + extracting memory via LLM)...")
            compaction_start_time = time.time()
            
            from . import config
            with OpenRouter(api_key=config.OPENROUTER_API_KEY) as client:
                sum_response = client.chat.send(
                    model=model_name,
                    messages=[{"role": "user", "content": combined_prompt}]
                )
                raw_content = sum_response.choices[0].message.content
                
            compaction_duration = time.time() - compaction_start_time
            compacted_summary, extracted_facts = _parse_compaction_response(raw_content)

            if extracted_facts:
                saved = 0
                superseded = 0
                skipped = 0
                pinned_cnt = 0
                for item in extracted_facts:
                    action = item.get("action", "ADD").upper()
                    text = item.get("text", "").strip()
                    old_text = item.get("old", "").strip()
                    is_pinned = bool(item.get("is_pinned", False))

                    if is_pinned:
                        pinned_cnt += 1

                    if action == "SUPERSEDE" and old_text:
                        db.delete_fact_by_text(old_text, replaced_by_text=text)
                        if text:
                            db.save_memory_fact(text, session_id, is_pinned=is_pinned)
                            superseded += 1
                    elif action == "ADD" and text:
                        if not db.fact_exists(text):
                            db.save_memory_fact(text, session_id, is_pinned=is_pinned)
                            saved += 1
                        else:
                            skipped += 1
                    elif action == "SKIP":
                        skipped += 1

                print(f"  [Memory]: LLM Actions -> Saved: {saved}, Superseded: {superseded}, Skipped: {skipped} (Auto-Pinned: {pinned_cnt})")

            # Trigger background consolidation if threshold crossed
            consolidate_memory(model_name)

            prev_archived_count, _ = db.get_compaction_state(session_id)
            db.update_compaction_state(session_id, prev_archived_count + newly_archived_count, compacted_summary)
            
            # Fetch active Pinned Core Memory + Hybrid Relevant Facts for last user query
            last_user_msg = conversation_history[-1].get("content", "") if conversation_history else ""
            pinned_facts = db.load_pinned_memory()
            relevant_facts = db.load_relevant_memory(last_user_msg)

            memory_sections = []
            if pinned_facts:
                pinned_block = "\n".join(f"- {f}" for f in pinned_facts)
                memory_sections.append(f"[Core Memory / Pinned Facts]:\n{pinned_block}")
            if relevant_facts:
                facts_block = "\n".join(f"- {f}" for f in relevant_facts)
                memory_sections.append(f"[Relevant Dynamic Facts]:\n{facts_block}")

            memory_ctx = ("\n\n" + "\n\n".join(memory_sections)) if memory_sections else ""

            updated_history = [
                {"role": "system", "content": f"{system_prompt}\n\n[Previous Context Summary]: {compacted_summary}{memory_ctx}"}
            ] + recent_messages
            print(f"  [System]: Compaction complete in {compaction_duration:.2f}s. Context compressed.\n")
            return updated_history
            
        except Exception as e:
            print(f"  [System Error]: Compaction failed ({e}). Using sliding window.")
            return recent_messages
            
    return conversation_history


# ---------------------------------------------------------------------------
# Long-term memory consolidation
# ---------------------------------------------------------------------------

CONSOLIDATION_THRESHOLD = 40   # trigger when unpinned facts exceed this
CONSOLIDATION_TARGET    = 20   # merge down to at most this many

CONSOLIDATION_PROMPT = """\
You are a memory-management system. Below is a list of {count} facts previously \
learned about the user across multiple conversations.

Your job is to produce a SHORTER, HIGHER-QUALITY list of at most {target} facts by applying these rules:

1. **Merge** facts that talk about the same topic into one richer sentence.
2. **Supersede**: When a newer fact contradicts an older one, keep ONLY the newer version.
3. **Deduplicate**: Drop facts that are near-identical in meaning, keeping the more detailed one.
4. **Preserve breadth**: Do not over-merge unrelated facts. Each output fact should cover one coherent topic.
5. **Keep it factual**: Do not invent new information. Only combine or prune what is given.

Return ONLY a JSON array of plain-text strings. No objects, no markdown fences, no commentary.
Example output: ["User's name is Nell", "User works as a DevOps engineer"]

--- FACTS ---
{facts}
"""


def consolidate_memory(model_name):
    """Merge and deduplicate long-term facts when unpinned facts exceed the threshold."""
    try:
        total = int(db.count_memory(include_pinned=False))
    except Exception:
        total = 0

    if total <= CONSOLIDATION_THRESHOLD:
        return

    facts_with_ids = db.load_all_memory_with_ids(limit=total)
    if not facts_with_ids:
        return

    target_ids = [item[0] for item in facts_with_ids]
    all_facts = [item[1] for item in facts_with_ids]
    numbered = "\n".join(f"{i+1}. {f}" for i, f in enumerate(all_facts))

    prompt = CONSOLIDATION_PROMPT.format(
        count=len(all_facts),
        target=CONSOLIDATION_TARGET,
        facts=numbered,
    )

    try:
        print(f"  [Memory]: {total} unpinned facts exceed threshold ({CONSOLIDATION_THRESHOLD}). Consolidating...")
        consolidation_start = time.time()

        from . import config
        with OpenRouter(api_key=config.OPENROUTER_API_KEY) as client:
            response = client.chat.send(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()

        json_str = _extract_json_array(raw)
        consolidated = json.loads(json_str)
        if not isinstance(consolidated, list) or len(consolidated) == 0:
            print("  [Memory]: Consolidation returned invalid data. Skipping.")
            return

        consolidated = [str(f).strip() for f in consolidated if str(f).strip()][:CONSOLIDATION_TARGET]

        db.replace_all_memory(consolidated, target_ids=target_ids)
        duration = time.time() - consolidation_start
        print(f"  [Memory]: Consolidated {total} → {len(consolidated)} unpinned facts in {duration:.2f}s.")

    except Exception as e:
        print(f"  [Memory]: Consolidation failed ({e}). Will retry next cycle.")