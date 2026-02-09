# Change Request Protocol (CR)

> **Когда использовать:** Owner хочет добавить/изменить функционал **вне текущей фазы**.

Ключевой принцип: **CR не ломает state machine и не обходит L2.**
Это управляемый мини-цикл через Analyst (и при необходимости через Architect).

## 0) Где живут CR (артефакты)

- `tasks/changes/CR-XXX-<slug>.md` — один файл на один change request (история + статус).
- `tasks/queue/CR-XXX-<role>.md` — задачи для ролей (создаёт Architect/Analyst).

`tasks/changes/**` — это **запись запроса**, не место для реализации.

## 1) Owner говорит

```
CHANGE REQUEST: <описание изменения>
```

Пример: `CHANGE REQUEST: добавить страницу /pricing с тарифами`.

## 2) Алгоритм оркестратора (L2-first, без обходов)

### Шаг 1: Синхронизируй main и прочитай фазу

1. `git checkout main && git pull --ff-only`
2. Прочитай `swarm_state.json.next_phase` (это текущая разрешённая роль).

### Шаг 2: Создай CR-файл (в PR, не напрямую в main)

Создай новый файл `tasks/changes/CR-XXX-<slug>.md` (XXX = следующий номер).

Шаблон:
```markdown
# CR-XXX: <title>

## Owner Request (verbatim)
> CHANGE REQUEST: <точная цитата запроса>

## Paused At
- phase: <swarm_state.json.next_phase at the moment of CR>
- date: <ISO timestamp>

## Architect Analysis (fill later)
- Summary:
- Affected roles: BACKEND / FRONTEND / BOTH / ARCHITECT
- Start role for mini-cycle:
- Requires QA_E2E: YES/NO (default YES if any UI or API change)

## Status
- [ ] Analyst: triage done
- [ ] Architect: plan + tasks created (if needed)
- [ ] Backend: merged (if needed)
- [ ] Frontend: merged (if needed)
- [ ] QA_E2E: merged (if needed)
- [ ] Analyst Final: approved
```

### Шаг 3: Переведи управление в Analyst gate (если CR вне Analyst/Architect фаз)

Если текущая `next_phase` **не** `ARCHITECT` и **не** `QA_CONTRACT`, делай CR через Analyst gate:

1. В той же PR (где добавлен `CR-XXX` файл) выполни переход:
   ```bash
   python3 swarm/transition_state.py \
     --role <role==current next_phase> \
     --to ANALYST_CI_GATE \
     --note "CR-XXX PAUSE: <short reason>. Phase work paused (not completed)."
   ```
2. Merge PR только через `gh_pr_gate.py` (required checks must be green).

Важно: это **pause/interrupt**. Мы специально фиксируем в `note`, что фаза не завершена.

### Шаг 4: Analyst triage (router)

Когда `next_phase=ANALYST_CI_GATE`:
1. Analyst читает `CR-XXX` файл и решает маршрут:
   - `ANALYST_CI_GATE -> ARCHITECT` если меняются контракты/архитектура/данные/границы модулей.
   - `ANALYST_CI_GATE -> BACKEND` если нужно API/логика.
   - `ANALYST_CI_GATE -> FRONTEND` если только UI.
2. Architect/Analyst создаёт задачи `tasks/queue/CR-XXX-<role>.md` для нужных ролей.

### Шаг 5: Мини-цикл по ролям (только нужные, но с gates)

Для каждой затронутой роли:
- роль делает PR → CI зелёный → merge;
- при FAIL запускается Fix Loop (та же роль чинит);
- после Dev-ролей обязательно Analyst gate;
- **если были изменения UI или API:** `QA_E2E` MUST быть выполнен и смёржен.

### Шаг 6: Возврат в основной flow

После закрытия CR, Analyst выбирает следующий шаг (обычно BACKEND/FRONTEND) и продолжает основной pipeline.

## 3) Частные случаи (чтобы не ломать пайплайн)

- Если `next_phase=ARCHITECT`: CR просто становится частью планирования. Заведи `CR-XXX` файл и продолжай.
- Если `next_phase=QA_CONTRACT`: обнови контракт/тесты с учётом CR и продолжай (без “перепрыгивания”).
- Если `next_phase=ANALYST_FINAL`: Analyst может направить сразу в `ARCHITECT/BACKEND/FRONTEND` по необходимости.

## 4) Железные правила CR

- **Никаких обходов L2:** нельзя менять base PR на непроверенную ветку, отключать checks, пушить в `main`.
- **CR не отменяет QA:** E2E нельзя пропускать.
- **Архитектор назначает роли, если затронута архитектура/контракты.**
