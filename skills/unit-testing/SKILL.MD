# Unit Testing Skill
Description: Use this whenever asked to write, run, or fix unit tests for any project, regardless of language (Python, JavaScript/TypeScript, Go, Java, Rust, etc).

## Rules for this task
0. Before reading any target file to understand what to test, follow the
    code-navigation skill's rules (get_file_info first, large view_file_lines
    ranges, no repeated list_directory calls). Do not read a file 6 times in
    150-line chunks when one get_file_info + 2-3 well-sized reads would do.
1. Detect the project's language and existing test framework before writing
   anything. Check for config/lockfiles first: `pytest.ini`/`pyproject.toml`
   -> pytest; `package.json` -> check for jest/vitest/mocha; `go.mod` -> Go's
   built-in `testing` package; `pom.xml`/`build.gradle` -> JUnit; `Cargo.toml`
   -> Rust's built-in `#[test]`. Never introduce a second test framework into
   a project that already has one.

2. Match the project's existing test file convention (naming, folder
   location, assertion style) rather than imposing a default. Look at one
   existing test file first if any exist.

3. NEVER let tests touch a real database, real files outside a temp
   directory, or make real network/API calls. Use the language's standard
   mocking/faking approach:
   - Python: monkeypatch / unittest.mock, tmp_path fixture
   - JS/TS: jest.mock() / vi.mock(), a temp dir via `fs.mkdtemp`
   - Go: interfaces + fake implementations, `t.TempDir()`
   - Java: Mockito, JUnit's `@TempDir`
   - Rust: trait objects + fakes, `tempfile` crate
   A fake must match the real dependency's interface/contract exactly
   (same method names, same call signature) so it fails loudly if the real
   interface changes.

4. Every bug that gets found and fixed in this session should get a
   regression test that would have caught it - not just a fix. Name the test
   after the bug's symptom, not generically (e.g. `test_archive_does_not_duplicate_on_reload`,
   not `test_archive_2`).

5. Test the failure path, not just the happy path: what happens when a
   dependency call throws/errors, when input is null/None/undefined, when
   an ID or path doesn't exist, when a boundary value is hit (empty list,
   max length, zero).

6. Keep tests fast and independent - no sleeps/timers as a substitute for
   proper synchronization, and no test may depend on another test's side
   effects or run order. Every test must pass alone AND in any order.

7. When fixing a bug elsewhere in the codebase, add or update its test in
   the same session - not as a separate follow-up. An unfixed bug without a
   regression test can silently reappear later.

8. Write the tests and run them once to confirm they at least execute
   without collection errors. Report the pass/fail count and list any
   failures with their error messages - but do NOT attempt to fix the
   source code or the test assertions afterward. Stop here and let the
   user decide what to do with the failures.
9. Always cleanup testing artifacts (like newly created temp files, local temp databases, or environment variables) after the test runs, ensuring no leftover garbage files in the project workspace.
10. Stay scoped to the target file only. Do not read sibling files 
   (config, __init__, other modules) unless the target file's imports 
   require understanding them. If unsure whether pytest/test deps are 
   installed, check pyproject.toml/requirements.txt ONCE at the very 
   start, before reading any other file.
11. Before writing any test, read the target file's own import statements 
first to know its ACTUAL dependencies. Never guess or add unrelated 
packages (e.g. requests, pandas) that the target file doesn't import.
12. When tests fail, fix ONE failure at a time: read only the relevant 
    test + relevant source function (not the whole file via read_local_file 
    or sub-agent), make the fix, re-run only that test file, then move to 
    the next failure. Do not scatter-search multiple failing test names at 
    once with search_in_files.
13. Never use shell redirects (2>&1, 2>nul, >, |) with execute_shell_command 
    - it runs with shell=False and redirects will not work; the tool 
    already returns both stdout and stderr separately.
14. When a test fails, first determine WHICH side is wrong - the test's
    assumption, or the source code's behavior - before fixing either one.
    Never weaken an assertion just to make it pass without understanding
    why it failed. State explicitly which side you're fixing and why.
15. When mocking a third-party library/SDK, only look at HOW the target file
    uses it (which methods/attributes it calls, in what shape) - do not read
    the library's own source code in .venv/site-packages, node_modules, or
    vendor directories to "verify" the interface. Match only the exact call
    pattern found in the target file being tested.