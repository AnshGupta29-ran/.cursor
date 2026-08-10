# Category template: File Storage / Document Platforms

Shared family shape for personal or team file vaults. Each forged prompt must define a
unique storage product — not a bare multer upload demo.

## Product family intent

Users authenticate, upload binary/text assets, organize them into hierarchies or
collections, search/filter them, download or share them, and understand quota usage.
The system must treat files as first-class domain objects with metadata and lifecycle.

## Identity & positioning (invent uniquely)

- Product name + audience (freelancers, clinics, classrooms, indie studios, legal teams)
- Primary content type emphasis (documents, media, mixed, scanned paperwork)
- Sharing model (private-only, link shares, team folders, expiring links)
- One distinctive twist (virus-scan stub, automatic OCR tags, retention policies,
  client-side encryption flag, dual personal/team roots)

## Required capability areas

### Identity & isolation
- Register/login/logout
- Per-user (or per-tenant) isolation of objects
- Profile or account settings relevant to storage (display name, default view)

### Object lifecycle
- Upload with size validation and content-type checks
- Download original bytes
- Rename, move, delete (soft-delete preferred if realistic)
- Folder/collection create/rename/delete
- Search by name and basic metadata filters

### Metadata & insights
- File size, type, uploaded_at, owner
- Storage usage statistics (used/limit)
- Recent files view

### Sharing & access (choose depth appropriate to seed)
- At least one sharing path OR explicit private-only with clear non-goal
- If sharing exists: permission levels and revoke

### Integrity & errors
- Friendly errors for oversized files, missing objects, unauthorized access
- Idempotent-ish delete/move behavior
- Safe path handling (no path traversal)

## UX expectations

- Clean dashboard: browse + upload prominent
- Breadcrumbs or equivalent navigation for folders
- Empty states for new accounts
- Progress or clear feedback on upload
- Responsive layout

## Data & persistence

Entities typically include: User, Folder, FileObject, ShareLink (optional), UsageQuota.
Prefer local disk or DB-backed blob paths suitable for demo; document where bytes live.
Never require cloud vendor accounts unless the seed explicitly asks.

## Quality & security

- Auth on all mutating routes
- Authorization checks on every object access
- Validate extensions/MIME where practical
- Automated tests for upload/download/authz negative cases

## Documentation & deliverables

- README with run + upload smoke steps
- Note max upload size and storage root
- Optional Postman/OpenAPI or equivalent for API-first variants

## Constraints & non-goals

- Not a full Dropbox clone with sync clients
- Not a CDN product
- Avoid fake “uploaded” rows without real stored bytes

## Acceptance criteria checklist (customize)

- [ ] Authenticated user can upload and download a real file
- [ ] Folder organization works end-to-end
- [ ] Search/filter returns expected objects
- [ ] Quota or usage display is accurate after uploads/deletes
- [ ] Unauthorized access is denied
- [ ] Automated tests cover happy path + one authz failure
- [ ] README reproduces a local demo

## Variation axes

Personal vs team · link sharing · preview panes · tagging · retention · encryption story ·
media-heavy vs docs-heavy · admin usage analytics

## Anti-clone rules

Do not regenerate the same “React + Express + Mongo Drive clone” wording each time.
Change domain vocabulary, folder semantics, and sharing rules so synthetic data diversifies.
