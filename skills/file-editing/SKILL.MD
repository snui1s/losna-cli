# File Editing Skill
Description: Use this whenever asked to modify, edit, update, or change content in an existing file.

## Rules for this task

1. FILE EDITING & TRUST: When you use the 'edit_local_file' or 'replace_in_file'
   tools to modify content, trust the success message returned by the tool. Do
   NOT call 'read_local_file', 'view_file_lines', or 'list_directory'
   immediately afterward to verify your action. Once the tool returns a success
   status, consider the task complete and reply to the user immediately.

2. TARGETED MODIFICATIONS: When asked to modify a specific function, variable,
   or block of code within an existing file, prefer using 'replace_in_file'
   over 'edit_local_file' to avoid accidentally destroying other parts of the
   file. Only use 'edit_local_file' (which overwrites/appends) when the user
   wants to replace the entire file content or append a new block, not when
   editing a specific existing part.

3. Before calling 'replace_in_file', make sure the 'old_text' you pass matches
   the file's actual current content exactly - if you haven't read the file
   yet in this task, read the relevant section first so the replacement
   doesn't silently fail to match.