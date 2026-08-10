# Category template: Finance / Productivity Apps

Family shape for personal finance, habits, and productivity trackers with private
user data, clear entities, and visualization. Each run needs a specific life domain.

## Product family intent

An authenticated user records life/work/money events, organizes them with categories
or projects, reviews trends, and stays motivated through goals/streaks/budgets.
Data isolation per user is mandatory.

## Identity & positioning (invent uniquely)

- Product name and life domain (budgeting, subscriptions, habits, study sessions, freelance ledger)
- Emotional tone (calm finance coach, strict budgeter, playful streaks)
- Primary insight (cashflow, streak heatmaps, project time burn)
- One twist (shared household view lite, envelope budgeting, recurring templates, mood tags)

## Required capability areas

### Accounts
- Register/login/logout
- Profile basics
- Strict per-user isolation

### Core records
- Create/edit/delete primary events (transactions, habits check-ins, tasks — per domain)
- Categories/tags/projects
- Dates, notes, optional attachments metadata

### Planning surfaces
- Budgets, goals, or recurring schedules as fits domain
- Progress indicators

### Insights
- Charts/summaries over selectable ranges
- Filters by category/project
- Export CSV/JSON preferred

### UX helpers
- Templates for common entries
- Empty-state educational copy
- Responsive layout

## Data & persistence

Entities vary by domain but typically: User, Category, Entry/Event, Goal/Budget,
RecurrenceRule, AttachmentMeta.
Local DB with migrations or auto setup documented.

## Quality & reliability

- Tests for isolation (user A cannot read user B)
- Validation for amounts/dates/streaks logic
- Totals on dashboards must match underlying entries

## Documentation & deliverables

- README with demo user and sample entries
- How charts are computed
- Reset/seed instructions

## Constraints & non-goals

- Not a bank integration / Plaid product unless seed explicitly requires mocks
- Not multi-currency trading platform
- Avoid vanity charts disconnected from data

## Acceptance criteria checklist (customize)

- [ ] User data is isolated
- [ ] CRUD on core entries works
- [ ] Category/organization works
- [ ] Insight views match stored data
- [ ] Goal/budget/streak logic works if specified
- [ ] Isolation + logic tests pass
- [ ] Local demo documented

## Variation axes

Finance vs habits vs tasks · household lite · recurring depth · export · mobile layout
emphasis · gamification level

## Anti-clone rules

Specialize domain language and insight widgets. Do not repeat the same “personal finance
tracker” section order and bullets verbatim across runs.
