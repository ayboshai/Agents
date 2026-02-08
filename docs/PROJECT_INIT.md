# Создание нового Swarm-проекта

## Quick Start

```bash
# 1. Переменные
PROJECT_NAME="my-project"
PROJECT_PATH="/var/lib/openclaw/workspace/$PROJECT_NAME"
GITHUB_REPO="owner/repo"

# 2. Создать директорию
mkdir -p "$PROJECT_PATH"
cd "$PROJECT_PATH"
git init

# 3. Скопировать CMAS-OS скелет
TEMPLATE="/var/lib/openclaw/workspace/codex-swarm-engine"
cp -r "$TEMPLATE/swarm" ./swarm
cp -r "$TEMPLATE/.github" ./.github
cp "$TEMPLATE/SWARM_CONSTITUTION.md" ./
cp "$TEMPLATE/SWARM_ARCHITECTURE.md" ./

# 4. Создать TASKS_CONTEXT.md
cat > TASKS_CONTEXT.md << 'EOF'
# Project Context

## Stack
- Language: 
- Framework: 
- Database: 

## Quality Criteria
- E2E mandatory
- No mocks
- No placeholders in production code

## Constraints
- 
EOF

# 5. Создать начальный swarm_state.json
cat > swarm_state.json << 'EOF'
{
  "schema_version": "1.0",
  "constitution_version": "2.0.0",
  "enforcement_level": "L2",
  "current_phase": "INIT",
  "next_phase": "ARCHITECT",
  "is_locked": false,
  "required_phase_sequence": [
    "ARCHITECT",
    "QA_CONTRACT",
    "BACKEND",
    "ANALYST_CI_GATE",
    "FRONTEND",
    "QA_E2E",
    "ANALYST_FINAL"
  ],
  "history": [],
  "task_id": "",
  "task_path": ""
}
EOF

# 6. Создать структуру tasks/
mkdir -p tasks/{queue,completed,feedback,reports,evidence/test-runs,logs}
touch tasks/logs/CI_LOGS.md
touch tasks/evidence/test-runs/.gitkeep

# 7. Первый коммит
git add .
git commit -m "feat: init CMAS-OS project skeleton"

# 8. Push на GitHub
git remote add origin "git@github.com:$GITHUB_REPO.git"
git push -u origin main
```

## После push: настроить GitHub

1. **Settings → Branches → Add rule** для `main`
2. **Require status checks:**
   - `swarm/state-guard`
   - `swarm/policy-guard`
   - `quality/no-mocks`
   - `quality/no-placeholders`
   - `tests/unit-integration`
   - `tests/e2e`
   - `attest/ci-summary`
3. **Strict mode:** ✅
4. **Require linear history:** ✅
5. **Do not allow bypassing:** ✅

## Зарегистрировать проект

```bash
# Добавить в реестр
echo "- name: $PROJECT_NAME" >> /var/lib/openclaw/workspace/SWARM_PROJECTS.md
echo "  path: $PROJECT_PATH" >> /var/lib/openclaw/workspace/SWARM_PROJECTS.md
echo "  repo: $GITHUB_REPO" >> /var/lib/openclaw/workspace/SWARM_PROJECTS.md

# Сделать активным
cat > /var/lib/openclaw/workspace/ACTIVE_SWARM_PROJECT.md << EOF
# Active Swarm Project
name: $PROJECT_NAME
path: $PROJECT_PATH
repo: $GITHUB_REPO
branch: main
EOF
```

## Проверка

```bash
cd "$PROJECT_PATH"
python3 swarm/validate_state.py --json
# Должно быть: "ok": true, next_phase: "ARCHITECT"
```
