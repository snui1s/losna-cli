# Code Navigation Skill
Description: Use this whenever a task requires reading exact code carefully - security review, refactoring, debugging, or understanding an existing file in detail.

## Rules for this task

1. SMART FILE INSPECTION: When dealing with large files, call 'get_file_info'
   first to check the size and total line count, rather than jumping straight
   into reading. This tells you how many 'view_file_lines' calls you'll
   actually need before you start.

2. Read the file in as FEW 'view_file_lines' calls as possible, using large
   ranges (e.g. 1-300, not 1-50 five times in a row). Do not guess line ranges
   blindly - use the total line count from 'get_file_info' to plan sensible
   chunks up front.

3. Do not call 'list_directory' more than once for the same folder within a
   single task. If you already listed a directory's contents, don't list it
   again unless the task specifically requires checking for new files that may
   have appeared since.

4. For files small enough to fit in one 'read_local_file' call (under the raw
   read threshold), just read the whole file directly rather than calling
   'get_file_info' + 'view_file_lines' - that's unnecessary overhead for
   small files.

5. When the task involves multiple related files (e.g. reviewing a module and
   its tests), plan out which files you need to read BEFORE starting, rather
   than discovering the need for another file mid-task and going back and
   forth.