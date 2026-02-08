# CMAS-OS Emergency Procedures

> ⚠️ **Только для Owner/Architect.** Эти процедуры нарушают обычный flow.

---

## 1. State Machine Corrupted

**Симптомы:** `validate_state.py` падает, history inconsistent, skip detected.

### Решение: Откат к последнему валидному состоянию

```bash
cd /path/to/project

# 1. Найти последний валидный коммит
git log --oneline swarm_state.json | head -10

# 2. Проверить каждый (начиная с последнего)
git show <SHA>:swarm_state.json | python3 -c "
import json, sys
state = json.load(sys.stdin)
print('next_phase:', state.get('next_phase'))
print('history entries:', len(state.get('history', [])))
"

# 3. Восстановить
git checkout <VALID_SHA> -- swarm_state.json
python3 swarm/validate_state.py --json

# 4. Если OK — коммит
git add swarm_state.json
git commit -m "fix: restore swarm_state.json from <VALID_SHA>"

# 5. Force push (требует временного отключения branch protection)
# GitHub → Settings → Branches → Edit rule → Disable temporarily
git push --force-with-lease
# GitHub → Re-enable branch protection
```

---

## 2. PR Stuck (CI не запускается)

**Симптомы:** PR открыт, но checks не появляются.

### Решение

```bash
# 1. Проверить workflows
cat .github/workflows/ci.yml | head -20

# 2. Триггернуть вручную (пустой коммит)
git commit --allow-empty -m "trigger: re-run CI"
git push

# 3. Или через GitHub UI:
# Actions → Select workflow → Run workflow
```

---

## 3. Branch Protection Locked Out

**Симптомы:** Нельзя смержить даже валидный PR.

### Решение (временное отключение)

1. GitHub → Settings → Branches → `main` → Edit
2. Uncheck все restrictions
3. Merge PR
4. **НЕМЕДЛЕННО** вернуть restrictions

---

## 4. Analyst Not Responding (SLA Breach)

**Симптомы:** `next_phase=ANALYST_*`, но нет ответа > 24h.

### Решение

```bash
# 1. Проверить текущую фазу
cat swarm_state.json | jq '.next_phase'

# 2. Если Owner может взять роль Analyst:
python3 swarm/transition_state.py \
  --role analyst \
  --to <NEXT_PHASE> \
  --note "Owner override: Analyst SLA breach (>24h)"
```

---

## 5. Нужно срочно откатить деплой

**Симптомы:** Баг в production, нужен hotfix вне swarm flow.

### Решение: Hotfix Branch

```bash
# 1. Создать hotfix от последнего стабильного
git checkout -b hotfix/critical-fix <STABLE_TAG>

# 2. Сделать минимальный fix
# ...

# 3. PR напрямую в main (временно отключить некоторые checks если нужно)
# После merge — синхронизировать swarm_state вручную

# 4. Добавить в history
python3 swarm/transition_state.py \
  --role orchestrator \
  --to <CURRENT_NEXT_PHASE> \
  --note "Hotfix applied outside swarm flow: <description>"
```

---

## 6. Полный Reset проекта

⚠️ **ДЕСТРУКТИВНО.** Удаляет всю swarm history.

```bash
cat > swarm_state.json << 'EOF'
{
  "schema_version": "1.0",
  "constitution_version": "2.0.0",
  "enforcement_level": "L2",
  "current_phase": "INIT",
  "next_phase": "ARCHITECT",
  "is_locked": false,
  "required_phase_sequence": [
    "ARCHITECT","QA_CONTRACT","BACKEND","ANALYST_CI_GATE",
    "FRONTEND","QA_E2E","ANALYST_FINAL"
  ],
  "history": [],
  "task_id": "",
  "task_path": "",
  "reset_note": "Full reset by Owner on YYYY-MM-DD"
}
EOF

git add swarm_state.json
git commit -m "reset: full swarm state reset"
# Требует force push с отключённым branch protection
```

---

## Contact Matrix

| Проблема | Эскалация |
|----------|-----------|
| CI не работает | Check GitHub Status Page |
| State corrupted | Owner/Architect |
| Analyst SLA | Owner |
| Security incident | Owner + Security Team |
