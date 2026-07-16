# Security Review Skill
Description: Use this whenever asked to review code for security vulnerabilities, do a security audit, or find exploits/weaknesses. Enforces evidence-based reporting to prevent hallucinated findings.

## Rules for this task

1. Never claim "no validation exists" or "no check whatsoever" in any function
   without first reading the ENTIRE function. If claiming X is missing, you must
   state: "Read function [name] lines [start]-[end], found no check for X."

2. Every vulnerability reported MUST include the actual quoted code (not just a
   line number). If you cannot quote the exact code, do not report it as a finding.

3. Before claiming a path-traversal vulnerability exists, search the file for
   these patterns first:
   - os.path.commonpath
   - os.path.realpath
   - os.path.abspath
   - startswith(base_dir)
   If any of these appear in the function, do NOT claim "no path validation
   exists" - instead evaluate whether the existing guard is sufficient, and
   explain why or why not with a concrete bypass example.

4. Always distinguish between these two different situations:
   - "No guard exists at all" (must be proven by reading the whole function)
   - "A guard exists but can be bypassed" (must include a concrete input/command
     that demonstrates the bypass)
   Do not conflate these - they have very different severity.

5. Severity levels:
   - Critical: exploitable with no existing guard at all (proven)
   - High: a guard exists but is bypassable with a realistic input (must show the bypass)
   - Medium: best practice gap, not directly exploitable
   - Low: code smell / maintainability, unrelated to security

6. Report format for each finding:
   ### [Severity] Vulnerability name
   - Function: name (lines X-Y)
   - Code:
     ```
     <exact quoted code>
     ```
   - Problem: <explanation>
   - Example exploit (if applicable): <concrete bypass>
   - Fix: <specific recommendation>

7. Before finalizing the report, self-check every line that says "no X" or
   "lacks X" or "whatsoever" - if there's no quoted code proving the absence,
   delete that claim or rephrase it as an open question instead ("should verify
   whether...").

Never use vague phrases like "ไม่มีการป้องกันเลย" or "whatsoever" without code
evidence backing it up.