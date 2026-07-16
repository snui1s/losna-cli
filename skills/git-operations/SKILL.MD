# Git Operations Skill
Description: Use this whenever the user asks to commit, push, check git status, or do any git-related task in this project.

## Rules for this task

1. When the user asks to commit and/or push changes, use the 'git_commit_and_push'
   tool directly. Do NOT run 'git add', 'git commit', 'git push' one by one via
   'execute_shell_command' - they will not chain with && and wastes tool calls.

2. Only use 'execute_shell_command' with 'git status' or 'git diff' first if you
   genuinely need to inspect changes before deciding on a commit message. Don't
   call these more than once per task unless something actually changed.

3. 'git_commit_and_push' always requires human confirmation before it actually
   runs (it returns CONFIRMATION_REQUIRED first). This is intentional - never
   try to bypass it or assume the user already agreed.

4. 'git add -A' inside 'git_commit_and_push' stages ALL changed files, including
   anything not in .gitignore. If you're unsure whether sensitive files (like
   .env, credentials, or large data dumps) might get swept in, run 'git status'
   first and flag it to the user before proceeding.

5. Do not chain shell commands with &&, ;, or | - execute_shell_command runs one
   command at a time by design (this prevents a class of parsing bugs). Call the
   tool once per command instead.

6. This project's remote default branch may not match the local branch name
   exactly (local: main, remote: master in some setups). If a push fails with an
   "upstream branch does not match" error, surface the exact git error to the
   user rather than guessing at a fix - branch/remote mismatches should be
   resolved by the user, not auto-corrected.