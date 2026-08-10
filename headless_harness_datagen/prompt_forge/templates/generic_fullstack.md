# Category template: Generic Full-stack Platforms

Fallback family for complete applications that do not cleanly fit a specialized
category. Still requires a sharp product identity — never a vague “build a web app”.

## Product family intent

Deliver a coherent full-stack MVP: authenticated users, a primary domain workflow,
persistence, a usable UI, docs, and tests. The platform must feel like a specific
product for a named audience.

## Identity & positioning (invent uniquely)

- Product name, audience, and painful job-to-be-done
- Primary workflow in one paragraph
- Secondary workflow that prevents “thin CRUD”
- One twist that would surprise a tutorial generator (policy engine lite, approvals,
  audit timeline, multi-step wizard, digest emails stub, etc.)

## Required capability areas

### Foundation
- Auth (or explicit single-operator local mode with rationale)
- Navigation + information architecture
- Persistent domain entities with validation

### Primary workflow (deep)
Describe states, actors, validations, and success criteria in detail.
Include at least two non-happy paths.

### Secondary workflow
 complementary feature that shares data with the primary workflow.

### Operator / settings
- Profile or workspace settings
- Sensible defaults

### API or server actions
- Clear server boundary
- Consistent error shape

## UX expectations

- Polished empty states
- Forms with inline validation
- Dashboard or home that reflects live data (not static cards)
- Responsive behavior

## Data & persistence

Invent a small but real schema (5–10 entities max unless seed is larger).
Document relationships and ownership/tenancy rules.

## Quality & reliability

- Tests for authz and primary workflow
- Seed data for demo
- No TODO-only stubs in critical path

## Documentation & deliverables

- README quickstart
- Domain model overview
- Acceptance walkthrough script

## Constraints & non-goals

- Not a design-system showcase
- Not microservices sprawl
- Not “AI features” without schema and evaluation

## Acceptance criteria checklist (customize)

- [ ] Named audience workflow is completable end-to-end
- [ ] Secondary workflow works against real data
- [ ] Authz/isolation rules hold
- [ ] UI home reflects database state
- [ ] Tests cover primary workflow
- [ ] Seed/demo path works
- [ ] README is sufficient for a cold start

## Variation axes

B2B vs consumer · approvals · audit · offline · notifications · multi-tenant lite ·
wizard vs dashboard-first UX

## Anti-clone rules

Force a niche. Reject generic SaaS Mad-Libs (“Manage your items efficiently”).
Every forged prompt must include domain nouns a stranger could google.
