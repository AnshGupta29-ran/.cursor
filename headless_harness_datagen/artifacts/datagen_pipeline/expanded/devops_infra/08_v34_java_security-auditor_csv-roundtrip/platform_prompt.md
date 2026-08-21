# VARIANT v34_java_security-auditor_csv-roundtrip - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `java`
- **user_persona**: `security_auditor`
- **novelty_hook**: `csv_roundtrip`
- **ui_surface**: `react_spa`
- **persistence**: `localstorage`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `java`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v34_java_security-auditor_csv-roundtrip`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v34_java_security-auditor_csv-roundtrip` when demoable.

---

## BASE PRD (honor unless mutated above)

# PLATFORM PROMPT — Proxyloom

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `java`
- **ui_surface:** `static_html`
- **persistence:** `csv_files`
- **complexity:** `hard`
- Do **not** rewrite this project in a different language.

## Complexity & fidelity lock (datagen)
- Complexity band: **hard**
- UI fidelity: HIGH — multi-view UI, stronger interaction, fuller charts/dashboard when UI is not api_only; all primary workflows clickable
- Effort cue: deepest; more entities, edges, and verification — still no wall-clock stop
- Anti-stub: FORBIDDEN as DONE: skeleton CRUD, unstyled link farms, claims of features without runnable paths
- **Never** stop for time/turns/“too big”; keep using tools until acceptance criteria pass, then print DONE.
- Match the locked `language_runtime`, `ui_surface`, `persistence`, and `testing_depth` from dimensions — do not homogenize to another stack.
- **Working demo required:** primary user actions must succeed in the browser/CLI (submit → visible result, seeded data, health check). Dead HTML shells are not DONE.
- If `ui_surface` is `api_only`, still ship an operator console/static page that calls the live API unless the PRD forbids UI entirely.
- **Build-first (anti time-waste):** Implement immediately from this PRD. Forbidden: WebSearch/WebFetch, browsing docs sites, winget/ripgrep installs for searching, Explore/research subagents, Grep/Glob fishing across sibling tasks. At most 2 targeted reads inside this task workdir before Write/Edit. Low = few files shipped fast — do not gold-plate.


## 1. Project Request / Product identity
**Proxyloom** is a single-binary Java 17 console that lets a solo developer design, lint, and download production-shaped **Nginx reverse-proxy configurations** without hand-editing `.conf` files. It manages a registry of upstreams (backend app ports on a home-lab VPS), TLS profiles, and server-block "sites", then weaves them into deterministic, downloadable `nginx.conf` output. Everything persists to plain CSV files. The UI is a static-HTML page served by the JDK's built-in HTTP server — no frameworks, no npm, no Docker.

Voice throughout (README, UI copy, comments): a pragmatic solo dev running three side-projects on one box, written first-person and terse.

## 2. Target users & primary jobs-to-be-done
- **Solo dev / home-labber** who self-hosts several apps behind one Nginx instance.
- Jobs: register a new app port → expose it as `app.example.com` → flip TLS on → lint the result → download the conf → keep an audit trail of what changed and when.

## 3. Core requirements / entities (CSV-backed)
- `upstreams.csv`: `name, host, port, scheme, weight, max_fails, health_path, tags`
- `tls_profiles.csv`: `name, mode(off|self-signed|letsencrypt-sim), cert_path, key_path, hsts, redirect_http`
- `sites.csv`: `hostname, listen_port, upstream_ref, tls_profile_ref, websocket, gzip, status(draft|published)`
- `renders.csv`: `render_id, seed, site_hostname, sha1, generated_at`
- `audit.csv`: `timestamp, actor(local), action, target, detail`
All CSV writes are sorted by primary key for byte-stable output.

## 4. Major feature areas
- **Inventory views**: ops-dense tables for upstreams, TLS profiles, sites; status colors documented (draft=amber, published=green, lint-error=red); filter by tag/status/hostname.
- **Detail drawer**: per-site view showing resolved upstream, effective TLS posture, and the rendered server-block snippet.
- **Conf renderer**: deterministic template emitting `upstream{}` + `server{}` blocks, `proxy_pass`, WebSocket upgrade headers, TLS directives per profile, `include`-ready layout; stable ordering (alphabetical) and SHA-1 checksum shown.
- **Linter (simulated `nginx -t`)**: rejects dangling `upstream_ref`, duplicate `listen_port`+`hostname` pairs, TLS `on` with empty cert/key paths, port out of 1–65535, invalid hostname syntax.
- **Actions**: add/edit/delete upstream, create site, toggle TLS profile per site, publish → writes `renders.csv` + audit row; delete blocked with explicit error when referenced by a site.
- **Download**: endpoint returns the full `.conf` as an attachment; also a "copy" view.
- **Read-only mode**: env var `PROXYLOOM_READONLY=1` disables mutating endpoints (HTTP 403) and badges the UI.

## 5. Domain-specific workflows
**Happy path**: `java -jar proxyloom.jar serve --seed 42` seeds fixture CSVs deterministically (names/ports derived from seed; clock fixed to a seed-derived base timestamp) → open `http://localhost:8471` → add upstream `blog:127.0.0.1:9001` → create site `blog.example.com:443` → attach `self-signed` TLS profile → preview render → lint passes → publish → download conf → audit row visible.

**Edge cases**: deleting a referenced upstream → 409 with the referencing site listed; TLS toggle with blank cert path → lint error panel, publish disabled; CSV directory missing → empty-state page with exact `serve --seed` fix hint; read-only mode → mutations rejected politely.

## 6. Data & persistence
CSV files under `./data/` are the sole source of truth; no database. Writes are atomic-ish (write temp + rename). Deterministic `--seed` must make two fresh runs produce byte-identical CSVs, rendered confs, and HTML snapshots.

## 7. UX / API surface
Single `index.html` + vanilla JS fetching small JSON endpoints (`GET/POST/DELETE /api/upstreams`, `/api/sites`, `/api/tls`, `GET /api/render?site=`, `GET /api/download`, `GET /api/audit`). Destructive deletes use a JS confirm dialog naming the target. One failing endpoint must not blank the page — per-panel error states.

## 8. Quality, security, reliability
No shelling out to real `nginx`; the linter is a faithful simulation and must be labeled "simulated nginx -t" in the UI. No external dependencies beyond the JDK. Paths are confined to `./data` and `./out` (no traversal). 2s response budget per endpoint.

## 9. Documentation & testing
- `README.md`: prerequisites (Java 17+ only), quickstart, safety notes, color semantics, first-person solo-dev tone.
- `proxyloom.sh`: one-command script — `seed | serve | render | smoke`.
- `notebooks/demo.ipynb`: bash cells driving the script through inspect → act → lint → download.
- **Smoke test** (`tools/smoke.sh` or JDK-only `SmokeTest.java`): boots server, asserts 200s, performs add-upstream + TLS toggle + publish, asserts linter rejects a dangling-ref site, asserts audit CSV grew. No JUnit downloads.
- **Visual diff** (`tools/visual_diff.sh`): regenerates the deterministic HTML snapshot and a sample rendered conf, diffs against checked-in files under `goldens/`, exits non-zero on drift. Goldens must be reproducible purely via `--seed`.

## 10. Constraints & non-goals
Not a real Nginx controller; no live reloads, no ACME, no multi-server fleets, no auth beyond the trusted-local + read-only flag. No "Hello World" placeholders; every screen must use authentic Nginx vocabulary (`proxy_pass`, `server_name`, `ssl_certificate`, `upstream`, `listen`).

## 11. Acceptance criteria
- [ ] `--seed 42` run twice yields byte-identical CSVs, confs, and HTML snapshot
- [ ] Inventory tables populate from CSV; filter works
- [ ] ≥4 actions work: add upstream, create site, toggle TLS, publish+download
- [ ] Referenced-upstream delete blocked with 409 + message
- [ ] Linter catches dangling ref, duplicate listen/host, TLS-without-cert
- [ ] Download returns a valid-looking `.conf` attachment with checksum shown
- [ ] Read-only mode returns 403 on mutations and badges UI
- [ ] Missing-data-dir empty state with fix hint
- [ ] `tools/smoke.sh` and `tools/visual_diff.sh` both exit 0
- [ ] README + notebook demo succeed as documented

## 12. Uniqueness / anti-clone constraints
Do not emit a generic CRUD or todo app. Required distinctive elements: seed-driven determinism (including fixed clock), CSV-only persistence with sorted keys, the simulated-and-labeled linter, checksum-stamped conf downloads, and the golden-file visual diff. Reject any solution needing Maven/npm downloads or Docker.
