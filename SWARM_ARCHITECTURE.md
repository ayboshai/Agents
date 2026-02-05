# Codex Swarm Architecture: Browser-Driven GitOps & TDD

> **Philosophy:** "Quality is not an act, it is a habit."
> This swarm operates on a strict **TDD (Test Driven Development)** and **Quality Gate** principle. No code moves forward without passing tests defined *before* the code was written.

## 1. System Overview

**Components:**
1.  **OpenClaw (Orchestrator):** Manages local files, browser relay, and git sync.
2.  **Browser Relay (Interface):** Connects to `chatgpt.com/codex` via Chrome Extension to execute Agent Personas.
3.  **GitHub (State & Exchange):** Serves as the message bus. Agents communicate by pushing/pulling files.
4.  **Codex (Worker):** The LLM execution engine running in the browser.

## 2. Workflow Lifecycle (The "Quality Loop")

The workflow is strictly sequential with feedback loops.

### Phase 1: Inception
1.  **Architect:**
    *   Reads User Request.
    *   Creates/Updates `TASKS_CONTEXT.md` (Project Rules, Stack, Constraints).
    *   Creates/Updates `00-structure.md` (File tree, API contracts).

### Phase 2: The Truth (Contract Testing)
2.  **QA (Contract Mode):**
    *   Reads `00-structure.md`.
    *   Writes **Failing Tests** (Red phase).
    *   *Rule:* Defines the "Definition of Done" via code. Tests must fail because implementation doesn't exist.

### Phase 3: Implementation (TDD)
3.  **Backend Developer:**
    *   Reads `TASKS_CONTEXT.md` and the *Failing Tests*.
    *   Writes Implementation Code to make tests **Green**.
    *   *Constraint:* Cannot modify tests (unless proved structurally wrong).

### Phase 4: Validation Gate
4.  **System Analyst (The Gatekeeper):**
    *   Reviews `CI_LOGS.md` (simulated or real).
    *   **IF FAIL:** Generates `fix_request.md` -> Returns to **Backend Developer**.
    *   **IF PASS:** Approves -> Triggers **Frontend Developer**.

### Phase 5: Visualization & E2E
5.  **Frontend Developer:**
    *   Reads `TASKS_CONTEXT.md` and API implementation.
    *   Builds UI.
6.  **QA (E2E Mode):**
    *   Writes End-to-End tests (Playwright/Selenium) to verify UI+API integration.
7.  **System Analyst:**
    *   Final Approval.

## 3. Dynamic Context Injection

All agents must adhere to the **Single Source of Truth**:
*   **File:** `TASKS_CONTEXT.md` (Root of repo).
*   **Content:** Tech Stack, Non-functional requirements (Speed vs Security), Libraries.
*   **Behavior:** Agents change their coding style based on this file.

## 4. Folder Structure (Repo)

```
/
├── TASKS_CONTEXT.md       # DYNAMIC: Project-specific rules (Stack, Speed, etc.)
├── tasks/
│   ├── queue/             # Pending tasks for Codex
│   ├── completed/         # Done tasks
│   └── feedback/          # Fix requests from Analyst
├── src/                   # Source code
├── tests/                 # QA Tests (Contract & E2E)
└── docs/                  # Architecture & API specs
```

## 5. Agent Personas (Summary)

*   **Architect:** Structural thinking, file tree planning.
*   **QA:** Destructive thinking, TDD evangelist. "Trust no one".
*   **Backend:** Solid code, security-first, test-compliant.
*   **Frontend:** UX-focused, component-based.
*   **Analyst:** Log parser, root cause analysis, strict gatekeeper.
