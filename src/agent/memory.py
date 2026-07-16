import os
import time
import json
from openrouter import OpenRouter
from . import db

def _parse_compaction_response(raw_text):
    """
    Split a combined 'SUMMARY: ... FACTS: [...]' response into (summary, facts).
    Falls back gracefully if the model doesn't follow the format exactly.
    """
    summary = raw_text.strip()
    facts = []

    if "FACTS:" in raw_text:
        summary_part, facts_part = raw_text.split("FACTS:", 1)
        summary_part = summary_part.strip()
        if summary_part.upper().startswith("SUMMARY:"):
            summary_part = summary_part[len("SUMMARY:"):].strip()
        summary = summary_part or summary

        facts_part = facts_part.strip()
        if facts_part.startswith("```"):
            facts_part = facts_part.strip("`")
            if facts_part.lower().startswith("json"):
                facts_part = facts_part[4:].strip()
        try:
            parsed = json.loads(facts_part)
            if isinstance(parsed, list):
                facts = [str(f).strip() for f in parsed if str(f).strip()]
        except Exception:
            facts = []
    elif raw_text.strip().upper().startswith("SUMMARY:"):
        summary = raw_text.strip()[len("SUMMARY:"):].strip()

    return summary, facts


def compact_memory(conversation_history, max_active_messages, keep_recent, model_name, system_prompt, session_id=None):
    """
    Function: Triggers memory compaction if active history exceeds max_active_messages.
    While compacting, also extracts any durable, reusable facts about the user (identity,
    preferences, ongoing projects) and saves them to the long-term memory table so they
    persist across sessions - not just within this one.

    All messages are already persisted to SQLite in real-time, so no disk offloading is needed.

    Returns:
        list: The updated conversation history (compacted or not).
    """
    if len(conversation_history) > max_active_messages:
        print("\n  [System]: Memory full. Triggering Compaction...")
        
        messages_to_compact = conversation_history[:-keep_recent]
        recent_messages = conversation_history[-keep_recent:]
        
        db.archive_messages(session_id, messages_to_compact)
        print(f"  [Storage]: Archived {len(messages_to_compact)} messages.")

        # Only count messages that actually came from the messages table -
        # the synthetic system-prompt entry (present at index 0 on the very
        # first compaction) was never a real DB row, so it must not shift
        # the reload watermark.
        newly_archived_count = sum(1 for m in messages_to_compact if m.get("role") != "system")
        
        combined_prompt = (
            "You are compacting a conversation history. Read the messages below and respond "
            "in EXACTLY this format (no extra text before or after):\n\n"
            "SUMMARY: <a concise summary of the key context and facts from these messages>\n"
            "FACTS: <a JSON array of PLAIN TEXT STRINGS only - NOT nested objects or dictionaries. "
            "Each item must be a complete, human-readable sentence, e.g. \"User's name is Nell\" or "
            "\"User enjoys jazz music and locked-room mystery novels\". Include facts, preferences, "
            "opinions, or interests the user has mentioned, even casual ones - not just formal "
            "identity facts. Never return {key: value} style objects, always full sentences as "
            "strings. Use [] only if truly nothing was worth remembering.>\n\n"
            "Messages:\n"
        )
        for msg in messages_to_compact:
            combined_prompt += f"{msg['role'].upper()}: {msg.get('content') or ''}\n"
            
        try:
            print("  [System]: Compacting context (summarizing + extracting memory)...")
            compaction_start_time = time.time()
            
            with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
                sum_response = client.chat.send(
                    model=model_name,
                    messages=[{"role": "user", "content": combined_prompt}]
                )
                raw_content = sum_response.choices[0].message.content
                
            compaction_end_time = time.time()
            compaction_duration = compaction_end_time - compaction_start_time

            compacted_summary, extracted_facts = _parse_compaction_response(raw_content)

            if extracted_facts:
                saved_count = 0
                for fact in extracted_facts:
                    if not db.fact_exists(fact):
                        db.save_memory_fact(fact, session_id)
                        saved_count += 1
                print(f"  [Memory]: Saved {saved_count}/{len(extracted_facts)} new long-term fact(s) (duplicates skipped).")

            # Persist the compaction watermark so reopening this session later
            # skips these already-processed messages instead of re-compacting
            # (and re-billing an LLM call for) the exact same history again.
            prev_archived_count, _ = db.get_compaction_state(session_id)
            db.update_compaction_state(session_id, prev_archived_count + newly_archived_count, compacted_summary)
            
            updated_history = [
                {"role": "system", "content": f"{system_prompt}\n\n[Previous Context Summary]: {compacted_summary}"}
            ] + recent_messages
            print(f"  [System]: Compaction complete in {compaction_duration:.2f}s. Context compressed.\n")
            return updated_history
            
        except Exception as e:
            print(f"  [System Error]: Compaction failed ({e}). Using sliding window.")
            return recent_messages
            
    return conversation_history