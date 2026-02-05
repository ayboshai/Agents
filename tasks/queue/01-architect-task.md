# TASK: CLONE LOGISOFT.RU WITH NEW CONTENT

## 1. OBJECTIVE
Create a pixel-perfect corporate website based on the design/structure of **logisoft.ru**, but populated with specific content for **"AB-Company"**.

## 2. REFERENCE (VISUAL & UX)
- **Target URL:** `https://logisoft.ru/`
- **Style:** Clean, Corporate, Blue/White palette, Trustworthy.
- **Components:**
  - Sticky Header with Contact Info.
  - Hero Section with Stats (Years on market, etc.).
  - Service Cards (Grid layout).
  - "About Us" Text Block.
  - Lead Generation Form (Footer/Modal).

## 3. TECH STACK (RECOMMENDED)
- **Framework:** Next.js (App Router)
- **Styling:** Tailwind CSS (for rapid cloning of logisoft's look).
- **Icons:** Lucide React.
- **State:** React Hooks.
- **Deployment:** Vercel-ready.

## 4. CONTENT (SOURCE OF TRUTH)
**Company Name:** AB-Company
**Contacts:** +79659903160, ticketbad@gmail.com, Telegram: @Ticket_lucky
**WhatsApp:** Link to +79659903160

### SECTIONS & TEXTS

#### Screen 1: Hero
- **Headline:** Автоматизация бизнеса с 1С
- **Subhead:** Мы помогаем бизнесу расти используя современные подходы. Наша цель - увеличить эффективность бизнеса за счет автоматизации процессов.
- **Stats:**
  - Выгодно (Работаем за стоимость, которую рассчитали изначально)
  - Надёжно (Более 12 лет опыта и 300+ успешно завершённых проектов)
  - В срок (Всегда выполняем задачи в заранее оговоренные сроки)
  - Продуманно (Советуем более эффективные решения)
- **Buttons:** "Оставить заявку", "Позвонить нам".

#### Screen 2: Services
- **Внедрение с нуля:** Установим и настроим под ваши нужды и бюджет.
- **Адаптация:** Донастроим систему или напишем новый функционал.
- **Аренда 1С:** Предоставим 1С в облаке без вашего сервера.
- **Маркетплейсы:** Автоматизируем торговлю (Wildberries, Ozon, etc.).

#### Screen 3: Marketplace Module
- **Title:** О модуле «Управление Маркетплейсами на 1С»
- **Description:** Синхронизация 1С с WB, Ozon, Yandex.Market. Ускоряет заказы, убирает рутину.
- **Benefits:** Экономия времени, Исключение ошибок, Рост прибыли.
- **Stats:** Рост валовой прибыли x3.9, Выручка x4.2, Товарооборот x4.5.

#### Screen 4: Cases (Critical Implementation Detail)
*Architect Note: These are detailed. Use a 'Card' preview on home, click to open full page or modal.*

- **Case 1:** Производитель бытовой техники (Москва).
  - Problem: Ручная обработка, штрафы.
  - Solution: Модуль маркетплейсов. Синхронизация за 1 неделю.
  - Result: Единый контроль, нет штрафов.

- **Case 2:** Поставщик БАДов (Тольятти).
  - Problem: 1С:УНФ без склада. Ручной перенос 300 товаров.
  - Solution: Настройка УНФ + Модуль. Перенос за 1 день.
  - Result: 1 менеджер ведет все площадки.

- **Case 3:** Одежда и обувь (Москва).
  - Problem: Бюджет <100к, страх покупки 1С.
  - Solution: Аренда 1С УТ + Честный Знак.
  - Result: Рост прибыли 50к -> 300к.

#### Screen 5: Contact Form
- **Fields:** Name, Phone, Message.
- **Action:** "Оставить заявку".

## 5. EXECUTION PLAN
1. **Architect:** Define `TASKS_CONTEXT.md` (Next.js/Tailwind) and File Tree (`components/Hero.tsx`, `components/Cases.tsx`, `data/content.ts`).
2. **QA:** Write tests checking if "AB-Company" exists in Header, if 3 cases are rendered, if phone number is correct.
3. **Backend/Frontend:** Implement the structure and insert text.

**START NOW.**
