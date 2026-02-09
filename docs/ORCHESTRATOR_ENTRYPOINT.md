# CMAS-OS Orchestrator Entrypoint

> **Цель:** Отправляй этот текст ассистенту при смене контекста.

---

## 0. Новый проект vs новая задача

Если пользователь сказал **"начинаем новый проект"**:
1. **STOP и уточни**: `project_name`, `path` (в `/var/lib/openclaw/workspace/`), `github owner/repo`, ветка (обычно `main`).
2. Создай проект строго по `/var/lib/openclaw/workspace/codex-swarm-engine/docs/PROJECT_INIT.md`.
3. Обнови `/var/lib/openclaw/workspace/SWARM_PROJECTS.md` и `/var/lib/openclaw/workspace/ACTIVE_SWARM_PROJECT.md`.
4. Убедись, что в новом репо `swarm_state.json.next_phase = ARCHITECT` и только после этого запускай Architect.

Если пользователь сказал **"новая задача"** (внутри текущего проекта):
- Проект НЕ меняется. Работаем строго по `swarm_state.json` в активном репо.

## 0. Выбери проект

Если проект не указан явно:
1. Читай `/var/lib/openclaw/workspace/ACTIVE_SWARM_PROJECT.md`
2. Если файла нет — спроси: "Какой проект активен?"
3. **НЕ делай ничего, пока не ясно где репо.**

---

## 1. Прочитай контекст (обязательно)

В корне репо:
1. `TASKS_CONTEXT.md` — стек, критерии
2. `SWARM_CONSTITUTION.md` — закон
3. `swarm_state.json` — `current_phase`, `next_phase`
4. `SWARM_ARCHITECTURE.md` — обзор

---

## 1.1 Канон = main (обязательно перед решениями)
Нельзя принимать решения по `swarm_state.json` в feature-ветке.
1. `git checkout main && git pull --ff-only`
2. Читай `swarm_state.json.next_phase` уже после этого.

---

## 2. Железные законы

| Закон | Суть |
|-------|------|
| **STATE MACHINE** | Роль = `swarm_state.json.next_phase`. Иначе STOP. |
| **L2 = TRUTH** | PASS/FAIL только из GitHub Actions |
| **NO SKIP** | `ARCHITECT→QA_CONTRACT→BACKEND→ANALYST_CI_GATE→FRONTEND→QA_E2E→ANALYST_FINAL` |
| **NO MERGE RED** | Нельзя мержить PR с красным CI |
| **NO MOCKS** | Моки = мусор |
| **NO BYPASS L2** | Запрещены stacked PR (смена base на непроверяемую ветку), отключение checks, прямой пуш в `main`. |
| **NO IMPROV** | Если блокер (CI/права/инструменты) — STOP и дай точный список причин и действий Owner’у. |

---

## 3. Основной цикл (L2)

```
1. Читай next_phase из swarm_state.json
2. Проверь (из корня репо проекта): python3 swarm/validate_state.py --role <role>
3. Задача MUST быть явной:
   - если пользователь дал путь задачи (например `tasks/queue/03-backend-task.md`) — используй его;
   - если путь не дан и в очереди несколько задач — STOP и спроси какую выполнять;
   - НЕ придумывай новые `tasks/queue/*` файлы “на ходу”, кроме фазы ARCHITECT.
4. Запусти роль через Codex → получи PR
4. HARD LOCK:
   python3 swarm/gh_pr_gate.py --pr <NUM> --merge
5. Если зелёный и смержен → git pull → повтори с п.1
```

---

## 3.1. Fallback на L1 (если GitHub недоступен)

Если `gh_pr_gate.py` не может связаться с API:
```bash
git fetch origin && git checkout <branch>
python3 swarm/validate_state.py --role <role>
python3 swarm/no_mocks_guard.py
python3 swarm/no_placeholders_guard.py
npm test && npm run test:e2e
# Если всё OK:
git checkout main && git merge <branch> && git push
```

---

## 4. Fix Loop

| Ситуация | Действие |
|----------|----------|
| CI красный | Та же роль чинит, новые коммиты в тот же PR |
| CI зелёный, Analyst reject | Analyst создаёт `fix_required.md`, откатывает фазу |
| **5 итераций без зелёного CI** | **STOP и эскалируй Owner'у с полным списком failures** |

---

## 5. Checklist перед "готово" (IDEAL CODE)

- [ ] Production-код без заглушек/placeholder
- [ ] Рефакторинг: компактность, лаконичность, чистота
- [ ] Убран AI-мусор
- [ ] Глубокие тесты (edge cases, errors, async)
- [ ] LARP-аудит (нет фейков, хардкода, глушения ошибок)
- [ ] Prod-чеклист (логи, конфиг, зависимости)
- [ ] Final audit

---

## 6. Completion Criteria

Проект завершён когда:
- `swarm_state.json.current_phase = "COMPLETE"`
- Все `tasks/queue/` → `tasks/completed/`
- E2E зелёные на staging
- Owner принял финальный signoff
