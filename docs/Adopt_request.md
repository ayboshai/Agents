# Adopt Existing Project Protocol

> **When to use:** you already have a working repo (not created by SwarmOS), but you want to manage changes via CMAS-OS.

Key principle: **do not “guess roles” on a legacy repo.**  
Instead, **bootstrap SwarmOS** and start with **ARCHITECT triage**.

## 1) Owner message (recommended format)

```
ADOPT PROJECT: <name>
repo: <github url>
server_path: /var/lib/openclaw/workspace/<name>
deploy: <how to deploy on server>
```

## 2) Orchestrator bootstrap steps (server)

1. Create a working copy under `/var/lib/openclaw/workspace/<name>` (so Danny/OpenClaw can access it).
2. Ensure ownership is writable by `openclaw:openclaw`.
3. Add CMAS-OS scaffolding into the repo:
   - `SWARM_CONSTITUTION.md` (copy from template)
   - `SWARM_ARCHITECTURE.md` (copy from template)
   - `TASKS_CONTEXT.md` (project-specific)
   - `swarm_state.json` with:
     - `current_phase=INIT`
     - `next_phase=ARCHITECT`
   - `swarm/` guard scripts (copy from template)
   - `config/personas/` (copy from template)
   - `tasks/` skeleton (copy from template)
   - `.github/workflows/ci.yml` (project-specific CI, but keep the required check names)
   - `.github/CODEOWNERS` (real owners)

## 3) First required task: ARCHITECT triage

Architect MUST:
1. read the legacy repo constraints and existing deploy/test commands,
2. read the Owner’s request/TZ,
3. decide “Affected Roles”,
4. create explicit `tasks/queue/*.md` files for the upcoming phases (no guessing later),
5. transition state to `QA_CONTRACT`.

## 4) Why this works

- The system never tries to auto-classify a legacy codebase.
- You still keep strict phase order and QA gates.
- The repo becomes self-contained (can be cloned elsewhere and still run under SwarmOS).
