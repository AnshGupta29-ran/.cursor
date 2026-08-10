# Meridian Stacks — Internal Research Library Circulation Console

## Complexity & fidelity lock (datagen)
- Complexity band: **low**
- UI fidelity: LOW — sparse layout, minimal CSS, few screens; still interactive (submit → visible result), never a dead form
- Effort cue: typically thinner than medium/hard (fewer files & screens), but never stop early
- Anti-stub: FORBIDDEN as DONE: blank pages, upload-with-no-effect, README-only, non-clickable mockups
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.


## 1. Project Request / Product Identity

**Meridian Stacks** is a procurement-grade, accessibility-first circulation system for a mid-size consulting firm's internal research library. The catalog holds three asset classes — **reference books** (30-day loans), **market research reports** (14-day loans, some under **embargo** until a release date), and **industry standards** (reference-only, never leave the library). Two roles: **Librarian** (knowledge operations) and **Member** (consultant/analyst). This is an operational tool an enterprise buyer would evaluate on auditability, keyboard accessibility (WCAG 2.2 AA intent), and zero-infrastructure deployment — not a public website.

## 2. Target Users & Jobs-to-be-Done

- **Librarian**: acquire/retire items, run the circulation desk (checkout/return on behalf), manage reservation queues, review the audit trail — entirely by keyboard.
- **Member**: find sources fast, borrow available items, join reservation queues, track own due dates and history.
- **Buyer lens**: every state change is auditable; every screen is operable without a mouse.

## 3. Core Entities

- `Item`: id, title, authors, assetClass (`book|report|standard`), topics[], year, abstract, status (`available|on_loan|reserved_ready|reference_only|embargoed|retired`), embargoUntil (nullable)
- `Member`: id, name, email, role (`librarian|member`)
- `Loan`: id, itemId, memberId, checkedOutAt, dueAt, returnedAt
- `Reservation`: id, itemId, memberId, queuedAt, status (`queued|ready|fulfilled|cancelled`)
- `Notice`: id, memberId, kind (`due_soon|overdue|hold_ready|embargo_released`), text, createdAt, read
- `AuditEvent`: id, at, actorId, action, itemId, detail

## 4. Major Feature Areas

- **Demo sign-in**: pick a seeded account (no passwords); role gates all restricted actions.
- **Catalog**: searchable, facet-filtered list (text query, assetClass, topic, status, year range) + detail view with availability and queue length.
- **Circulation desk (librarian)**: checkout, return, add/edit/retire items, release embargoes early.
- **Self-service (member)**: borrow available items, reserve items on loan, cancel own reservations, view own loans/history/notices.
- **Notifications tray**: badge count, aria-live announcements; auto-generated due-soon (≤3 days), overdue, hold-ready, embargo-released notices.
- **Audit log (librarian-only)**: append-only, filterable by actor/action.

## 5. Domain Workflows (happy path + edge cases)

1. **Borrow & overdue**: Member borrows a report → due date = today+14. Edge: member with any overdue loan is blocked from new checkouts with a clear message; return clears the block and logs `AuditEvent`.
2. **Reservation queue**: Item on loan → member reserves (position shown). Edge: duplicate reservation by the same member rejected; on return, first queued member gets `hold_ready` + status `reserved_ready` with a 48-hour hold window; expiry auto-passes to next in queue.
3. **Embargoed report**: New report with `embargoUntil` appears in catalog as `embargoed` — visible, not borrowable. Edge: borrow attempt blocked with release date shown; on/after the date (or librarian early-release) status flips and waitlisted members get `embargo_released` notices. Reference-only standards always reject checkout.

## 6. Data & Persistence

- **localStorage is the system of record**, keys namespaced `meridian.v1.*`, each entity a JSON collection.
- First run seeds from bundled `seed.json` (≥10 items across all three asset classes, 5 members, 1 active overdue loan, 1 queued reservation, 1 embargoed report). A "Reset demo data" action (and CLI flag) re-seeds.
- The Python process only serves static assets and seed data; no server-side database. Must work fully offline.

## 7. UX / API Surface

- **Runtime**: Python 3.10+. CLI entry: `python -m meridian run` opens a **desktop window** (pywebview, the single declared dependency); `python -m meridian serve` serves the same app at `http://127.0.0.1:8765` for smoke checks; `python -m meridian reset`.
- **Accessibility-first keyboard UX (the differentiator, non-negotiable)**: full operability without a mouse; logical tab order; visible focus ring; skip-to-content link; landmark roles; roving-arrow-key navigation in the catalog list; `Enter` opens detail; shortcuts — `/` focus search, `?` shortcut-help dialog, `n` new item (librarian), `Esc` close dialog with focus returned to trigger; notices announced via `aria-live="polite"`; respects `prefers-reduced-motion`; every control has an accessible name and validation errors are announced and linked to fields.

## 8. Quality, Security, Reliability

- Illegal transitions blocked in one shared state-machine module (e.g., checkout of `embargoed`/`reference_only`/`on_loan` items, double reservation, return of non-loaned item).
- Form validation with inline, screen-reader-announced messages (title, authors, assetClass, year required; embargo date only on reports).
- No external network calls, CDNs, or trackers.

## 9. Documentation & Testing

- `README.md`: product summary, run instructions, seeded accounts, 5-minute walkthrough of all three workflows, keyboard shortcut table, data-reset steps.
- `python -m meridian smoke` (stdlib only): boots the server, asserts index/assets/seed return 200 with expected markers, exits non-zero on failure (**browser_smoke** path: app must also pass a manual open-and-click-through).
- **Integration-light**: a `tests.html` page that runs the state-machine module against an isolated localStorage namespace and reports pass/fail for: overdue block, queue promotion on return, embargo release, duplicate-reservation rejection, role permission denial.

## 10. Constraints & Non-Goals

- Honor the stack lock: Python runtime, desktop-window UI, localStorage persistence. **No Django, no SQLite/Postgres, no server DB, no REST backend** despite the original request wording — the server only hosts static files.
- Non-goals: SSO/passwords, fines/payments, barcode hardware, multi-branch, email delivery, mobile layout polish.
- ≤ ~8 source files; no build step; no lorem ipsum.

## 11. Acceptance Criteria

- [ ] `run` opens a desktop window; `serve` + `smoke` pass from a clean checkout.
- [ ] Seeded librarian and member accounts; members cannot reach librarian actions (UI hides and logic rejects).
- [ ] All three workflows complete, including every listed edge case, with no console edits.
- [ ] Search + ≥3 facet filters return correct subsets.
- [ ] Every screen completes end-to-end by keyboard alone; focus visible; notices announced via live region.
- [ ] `tests.html` reports all integration checks green; audit log records each state change.
- [ ] Reset restores seed data.

## 12. Uniqueness / Anti-Clone Constraints

- Use domain-authentic vocabulary throughout (`embargo`, `hold window`, `reference-only`, `circulation desk`, `queue position`) — generic "Book title / borrow button" tutorial framing is a defect.
- The three asset classes with differentiated loan policies and the embargo-release twist must be visible in seed data and UI, not just code.
- Accessibility must be demonstrably real: hand-auditable tab order, working shortcuts, and live-region announcements — not ARIA sprinkled on a mouse-only UI. No placeholder pages, no dead buttons, no lorem ipsum.
