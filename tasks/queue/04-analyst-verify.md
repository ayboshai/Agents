# TASK: SYSTEM ANALYSIS & QUALITY GATE

## 1. OBJECTIVE
Review the Build and Test logs to determine if the implementation meets the Quality Contract.

## 2. INPUT
- `tasks/logs/CI_LOGS.md` (The actual output from the test runner).
- `tests/` (The contracts that were run).
- `TASKS_CONTEXT.md` (The project rules).

## 3. DECISION LOGIC
**IF `CI_LOGS.md` contains "FAIL" or "Error":**
- Generate `tasks/feedback/fix_required.md`.
- List specific failing tests.
- Blame the component/data responsible.
- INSTRUCTION: "Backend Developer, fix the code to satisfy these tests."

**IF `CI_LOGS.md` contains "PASS" (and no fatal errors):**
- Generate `tasks/completed/PROJECT_STATUS.md`.
- Content: "All Systems Operational. Ready for Deployment."
- Summary of what passed (Data, Components, Pages).

## 4. EXECUTION RULES
- Be strict. Warnings are acceptable, Errors are not.
- Do not hallucinate success. Trust the log file.

## 5. OUTPUT
- `tasks/feedback/fix_required.md` OR `tasks/completed/PROJECT_STATUS.md`
