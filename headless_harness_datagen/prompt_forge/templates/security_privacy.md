# Category template: Security / Privacy Tools

Family shape for vaults, credential managers, and privacy-sensitive utilities.
Security properties are product features — not afterthoughts.

## Product family intent

Users protect secrets or sensitive records behind strong local authentication, with
encryption at rest, careful clipboard/memory handling, and clear threat-model limits.
The tool should be usable daily while failing closed on auth errors.

## Identity & positioning (invent uniquely)

- Product name and threat context (personal passwords, team API tokens, family wifi secrets)
- Client form factor (desktop GUI, local web, CLI+TUI) matching the seed
- Trust boundary statement (local-only vs optional sync — default local-only)
- One twist (duress PIN, auto-lock, Shamir split backup, per-entry policies, audit timeline)

## Required capability areas

### Unlock & session
- Master credential creation and unlock
- Auto-lock after inactivity (configurable)
- Failed attempt handling

### Cryptography (practical, documented)
- Encryption for vault contents (algorithm named)
- Key derivation from master secret (KDF named)
- No plaintext secrets written to logs

### Secret records
- CRUD for entries with fields appropriate to domain
- Categories/tags and search
- Password/secret generator with strength indicator when relevant
- Clipboard copy with automatic clear policy

### Backup & portability
- Export/import encrypted or documented format
- Warnings about plaintext export if offered

### Safety UX
- Confirmations for destructive actions
- Visible lock state
- Recovery guidance if master credential lost (honest: often impossible — say so)

## UX expectations

- Minimal chrome, high signal
- Keyboard-friendly primary flows
- No surprise network calls unless seed requires and user consents

## Data & persistence

Entities: VaultMeta, LockedBlob/Entries, Category, AuditEvent (optional).
Store files in a well-defined local path; document format version.

## Quality & reliability

- Unit tests for encrypt/decrypt roundtrip and KDF basics
- Tests rejecting wrong master credentials
- Avoid custom novel crypto; prefer well-known libraries

## Documentation & deliverables

- Threat model section (what is / isn’t protected)
- README with create-vault → add-entry → lock → unlock demo
- Explicit non-goals (not FIPS certified, etc.)

## Constraints & non-goals

- Not a cloud password manager SaaS unless seed demands
- Not malware/red-team tooling
- Do not invent home-grown “unbreakable” crypto claims

## Acceptance criteria checklist (customize)

- [ ] Vault cannot be read without master credential
- [ ] Entries persist across restart when unlocked correctly
- [ ] Generator + strength indicator work if required
- [ ] Clipboard auto-clear behavior is demonstrable or documented with timer
- [ ] Wrong password fails closed
- [ ] Crypto roundtrip tests pass
- [ ] Threat model documented

## Variation axes

Desktop vs local web · team shared vault · API token focus vs passwords · audit richness ·
backup ritual · auto-lock strictness

## Anti-clone rules

Do not recycle the same “PySide6 AES vault” paragraph set. Vary entry schemas, unlock
policies, and backup stories for diversity.
