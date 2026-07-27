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
            
            from . import config
            with OpenRouter(api_key=config.OPENROUTER_API_KEY) as client:
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

            # If facts have piled up past the consolidation threshold,
            # merge them down into a tighter set while we're already here.
            consolidate_memory(model_name)

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


# ---------------------------------------------------------------------------
# Long-term memory consolidation
# ---------------------------------------------------------------------------

CONSOLIDATION_THRESHOLD = 40   # trigger when total facts exceed this
CONSOLIDATION_TARGET    = 20   # merge down to at most this many

CONSOLIDATION_PROMPT = """\
You are a memory-management system. Below is a list of {count} facts previously \
learned about the user across multiple conversations.

Your job is to produce a SHORTER, HIGHER-QUALITY list of at most {target} facts by applying these rules:

1. **Merge** facts that talk about the same topic into one richer sentence.
   Example: "User likes React" + "User uses React with TypeScript" → "User uses React with TypeScript"
2. **Supersede**: When a newer fact contradicts an older one, keep ONLY the newer version.
   Example: "User likes React" + "User switched from React to Vue" → "User switched from React to Vue"
3. **Deduplicate**: Drop facts that are near-identical in meaning, keeping the more detailed one.
4. **Preserve breadth**: Do not over-merge unrelated facts. Each output fact should cover one coherent topic.
5. **Keep it factual**: Do not invent new information. Only combine or prune what is given.

Return ONLY a JSON array of plain-text strings. No objects, no markdown fences, no commentary.
Example output: ["User's name is Nell", "User works as a DevOps engineer"]

--- FACTS ---
{facts}
"""


def consolidate_memory(model_name):
    """Merge and deduplicate long-term facts when they exceed the threshold.

    Calls the LLM once to produce a tighter set, then atomically replaces
    the old facts in the DB.  Silently skips if the count is still below
    the threshold or if the LLM call fails (non-critical path)."""
    total = db.count_memory()
    if total <= CONSOLIDATION_THRESHOLD:
        return

    all_facts = db.load_all_memory(limit=total)  # uncapped load for consolidation
    numbered = "\n".join(f"{i+1}. {f}" for i, f in enumerate(all_facts))

    prompt = CONSOLIDATION_PROMPT.format(
        count=len(all_facts),
        target=CONSOLIDATION_TARGET,
        facts=numbered,
    )

    try:
        print(f"  [Memory]: {total} facts exceed threshold ({CONSOLIDATION_THRESHOLD}). Consolidating...")
        consolidation_start = time.time()

        from . import config
        with OpenRouter(api_key=config.OPENROUTER_API_KEY) as client:
            response = client.chat.send(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if the model wraps its answer
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

        consolidated = json.loads(raw)
        if not isinstance(consolidated, list) or len(consolidated) == 0:
            print("  [Memory]: Consolidation returned invalid data. Skipping.")
            return

        # Safety: cap at target to prevent model from ignoring the instruction
        consolidated = [str(f).strip() for f in consolidated if str(f).strip()][:CONSOLIDATION_TARGET]

        db.replace_all_memory(consolidated)
        duration = time.time() - consolidation_start
        print(f"  [Memory]: Consolidated {total} → {len(consolidated)} facts in {duration:.2f}s.")

    except Exception as e:
        # Consolidation is best-effort; never block the main flow
        print(f"  [Memory]: Consolidation failed ({e}). Will retry next cycle.")