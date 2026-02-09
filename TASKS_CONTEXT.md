# TASKS_CONTEXT

## Project Type
Describe the product in 1-3 sentences.

## Stack
- Language:
- Framework:
- Storage:
- Testing:
- E2E:

## Critical Constraints
1. **Mandatory E2E:** the `tests/e2e` suite MUST exist and run in CI.
2. **No mocks for internal logic:** test real code paths; do not replace the system-under-test with mocks.
3. **No stubs/placeholders:** production paths must be fully implemented.
4. **Evidence-based gates:** PASS/FAIL comes from CI required checks (L2) or captured stdout/stderr (L1).

## Non-Functional Targets
- Reliability:
- Security:
- Performance:

