# Category template: CMS / Content / Catalog Platforms

Family shape for libraries, blogs, catalogs, and editorial systems. Each forged prompt
must define a concrete content domain and roles — not a blank “Post title / body” blog.

## Product family intent

Authenticated roles create, organize, discover, and lifecycle-manage content objects
(articles, books, listings, learning modules, etc.). Search, permissions, and audit-ish
history matter as much as the create form.

## Identity & positioning (invent uniquely)

- Product name and content domain (public library, indie magazine, course notes, museum)
- Roles (e.g. librarian/student, editor/author/reader, curator/visitor)
- Discovery emphasis (search facets, collections, recommendations-lite)
- One twist (reservations, embargo dates, peer review, featured collections, citations)

## Required capability areas

### Accounts & roles
- Auth flows appropriate to roles
- Permission matrix for create/edit/publish/borrow/delete style actions
- Isolated personal state where relevant (reading history, drafts)

### Content lifecycle
- Create/update/archive (or borrow/return if library-like)
- Statuses (draft/published/archived OR available/loaned/reserved)
- Validation rules for required fields

### Catalog & search
- List + detail views
- Filters (category, tag, status, date, owner)
- Full-text or field search

### Workflows
Define 2–3 end-to-end workflows unique to the domain, including edge cases
(overdue, double reservation, unpublished visibility, etc.).

### Notifications / signals (lightweight OK)
- In-app notices for due dates, publish approvals, or moderation

## UX expectations

- Role-aware navigation
- Admin/staff console distinct from consumer browse when roles differ
- Empty catalog onboarding
- Accessible forms and clear validation messages

## Data & persistence

Entities often include: User, Role, ContentItem, Category/Tag, Loan/Reservation or
Revision, AuditEvent.
Use SQLite/Postgres/local DB suitable for demo; migrations or auto-schema documented.

## Quality & reliability

- Unit/integration tests for permissions and primary workflow
- Prevent illegal state transitions
- Sensible indexes/filters performance for small demos

## Documentation & deliverables

- README with seeded users/roles and demo walkthrough
- Content model overview
- How to reset demo data

## Constraints & non-goals

- Not a headless CMS mega-platform
- Not a full DAM/CDN
- Avoid lorem-only fixtures without realistic field semantics

## Acceptance criteria checklist (customize)

- [ ] Role permissions enforce restricted actions
- [ ] Core lifecycle workflow completes without manual DB edits
- [ ] Search/filter returns correct subsets
- [ ] Edge-case rules from the prompt are implemented
- [ ] Seeded demo accounts work out of the box
- [ ] Automated tests cover authz + primary workflow
- [ ] README enables local reproduction

## Variation axes

Domain · role complexity · reservation vs publishing · moderation · public vs private
catalog · citation/metadata richness

## Anti-clone rules

Avoid repeating the same library-borrow prompt text. Change item types, policies, and
staff workflows so each synthetic CMS differs meaningfully.
