# VARIANT v08_cpp_open-source-maintainer_idempotent-retries - synthetic expansion of the base PRD below

## Dimension mutations (MANDATORY - override base locks if they conflict)
- **language_runtime**: `cpp`
- **user_persona**: `open_source_maintainer`
- **novelty_hook**: `idempotent_retries`
- **ui_surface**: `dashboard_charts`
- **persistence**: `csv_files`
- **complexity**: `low`
- **session_shape**: `multi_turn_repair`
- **delivery**: `cli_entry_plus_ui`

## Language lock
- Implement primarily in `cpp`.
- Do not homogenize to Python unless language_runtime is python.

## Subtask acceptance extras
- Ship a distinct product codename suffix `-v08_cpp_open-source-maintainer_idempotent-retries`.
- Keep the same core job-to-be-done as the base PRD.
- Add one stress scenario from the mutations.
- README: run command, seed data, mutations applied.
- Full working demo required (not a stub).
- MUST include `scripts/smoke.py` (or `npm run smoke`) exiting 0.
- MUST include seed/fixture/synthetic sample data (`fixtures/` or `data/`).
- Outer VALIDATE gate rejects stubs before mark-done.
- Print `DONE <parent>__v08_cpp_open-source-maintainer_idempotent-retries` when demoable.

---

## BASE PRD (honor unless mutated above)

# ClerkLens — Cited Q&A Over Municipal Meeting Packets

## LANGUAGE LOCK (datagen)
- **language_runtime (MANDATORY):** `python`
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


## 1. Project Request / Product Identity
Build **ClerkLens**, a local, single-user research assistant built by a solo civic-tech developer for reading municipal meeting records. It ingests agendas, minutes, and ordinance excerpts (`.txt`, `.pdf`), chunks and indexes them locally, and answers questions with **extractive, citation-backed answers** — every answer sentence carries chunk citations, and the system **abstains rather than hallucinates** when retrieval confidence is low. The LLM layer is a **clearly labeled deterministic stub** (template + extractive sentence selection), so the repo runs fully offline with zero model downloads; a real LLM can be plugged in later via a documented seam. Human-in-the-loop stance: all answers are *drafts with provenance*, never auto-final.

## 2. Target Users & Jobs-to-be-Done
A solo developer / local journalist / civic watchdog who asks things like *"What was the vote on the short-term rental ordinance?"* and needs to (a) get a traceable answer fast, (b) click through to the exact source passage, and (c) keep an auditable history of every question asked.

## 3. Core Entities (CSV-backed, `data/` dir, stdlib `csv` only)
- `documents.csv`: doc_id, filename, doc_type (agenda|minutes|ordinance), meeting_date, n_chars, sha256, ingested_at
- `chunks.csv`: chunk_id, doc_id, seq, start/end char, page (if PDF), text, token_count
- `queries.csv`: query_id, asked_at, question, seed, profile, top_k
- `answers.csv`: answer_id, query_id, status (answered|abstained), confidence_band, answer_text, cited_chunk_ids, latency_ms
- `request_log.csv`: ts, endpoint, status_code, ms

Deterministic IDs: `doc_id = sha256(content)[:12]`; `chunk_id = {doc_id}-c{seq:04d}`. CSVs are the source of truth; the search index is rebuilt from them at startup.

## 4. Major Feature Areas
- **Ingestion**: HTML form + CLI; validates extension, size ≤ 2 MB, non-empty extractable text. Corrupt or scanned (no-text-layer) PDFs rejected with distinct messages. Duplicate content detected via sha256 → skipped with notice, no duplicate rows.
- **Chunking**: deterministic ~450-char windows, 80-char overlap, paragraph-boundary aware; pure function of (text, seed).
- **Index/retrieval**: TF-IDF + cosine similarity (pure-Python preferred; scikit-learn allowed if pinned). Ties broken by ascending chunk_id for stability.
- **Answer composer (STUB — labeled in UI banner and README)**: picks top-k sentences from chunks above threshold, wraps them in a fixed template with `[chunk_id]` citations; confidence band High/Medium/Low from score margins; abstains when top score < profile threshold.
- **Threshold profiles**: `strict` / `balanced` / `exploratory` presets (k, min_score).
- **Provenance UX**: citation chips on each answer link to a chunk view with the source text highlighted; `/history` lists all past Q&A.
- **Visual-diff snapshot mode**: `scripts/snapshot.py --seed 42` loads fixture corpus, asks 3 canned questions, renders canonical HTML to `snapshots/run_<seed>.html` — byte-identical across runs with the same seed (verify via sha256sum).

## 5. Domain Workflows
**Happy path**: serve → upload sample minutes PDF → ask about a roll-call vote → get an answer with 2–4 citation chips, confidence band, and latency → click a chip → highlighted source chunk → entry persisted in history.
**Edge cases**: `.docx` → 400 with plain message; scanned PDF → distinct rejection; question with zero corpus overlap ("quantum entanglement") → abstain card, not a fabricated answer; duplicate upload → notice only; empty/punctuation-only question → validation error.

## 6. Data & Persistence
CSV files only — no SQLite, no ORM, no vector DB. Atomic-ish writes (temp file + rename). Fixture corpus in `fixtures/`: 2 `.txt` + 1 small text-based `.pdf` (each < 60 KB), authentically municipal (agenda, minutes with motions/roll-call votes, ordinance excerpt) — no lorem ipsum.

## 7. UX / API Surface
Static HTML only: server-rendered pages (Flask suggested, stdlib templates), no JS framework, no build step, minimal inline CSS. Pages: Upload, Ask, Answer detail, History, Chunk view. Stub banner on every answer: *"Stub LLM — extractive only, no generative model."*
Endpoints, documented in README with working curl examples: `POST /ingest` (multipart), `POST /ask`, `GET /history`, `GET /chunk/<chunk_id>`, `GET /healthz`. All requests logged to `request_log.csv`.

## 8. Quality, Security, Reliability
`--seed` flag (default 42) on CLI + notebook: same corpus + question + seed → identical CSV rows and identical snapshot bytes. Never crash on empty/partial files; user errors → 4xx with plain-language messages. Sanitize filenames; enforce size cap; no network calls at runtime; no secrets. Cold start shows a guided empty state with a "load sample corpus" action.

## 9. Documentation & Testing
README: quickstart (`pip install -r requirements.txt`, `python scripts/ingest.py fixtures/`, `python scripts/serve.py`), curl examples, pipeline description, **Limitations** (stub is extractive; English tokenization; scanned PDFs unsupported; lexical TF-IDF ≠ semantic search; single-user), how to swap in a real LLM, reproducibility notes. `notebooks/walkthrough.ipynb` runs top-to-bottom offline demonstrating ingest → ask → citations with the seed respected. Smoke tests only (pytest, < 10s total, no downloads): validation rejects bad files; fixture ingest yields expected chunk count; ask returns citations; abstention case; two snapshot runs produce identical bytes.

## 10. Constraints & Non-Goals
Python 3.10+. Locked: static HTML UI, CSV persistence, notebook + script delivery. No GPU/torch/transformers, no cloud APIs, no auth (single-user local tool), no JS frameworks, no model training, no multi-turn chat memory, not an MLOps platform.

## 11. Acceptance Criteria
- [ ] Valid `.txt`/`.pdf` uploads are chunked, indexed, and visible in the UI
- [ ] Unsupported/corrupt/scanned/oversize inputs rejected with distinct messages
- [ ] Duplicate upload detected; no duplicate CSV rows
- [ ] Ask returns extractive answer with ≥1 chunk citation and confidence band, or abstains below threshold
- [ ] Citation click-through shows the highlighted source chunk
- [ ] History survives server restart (reloaded from CSV)
- [ ] `snapshot.py --seed 42` run twice → identical bytes (sha256 match)
- [ ] Notebook executes top-to-bottom offline
- [ ] pytest smoke suite passes in <10s with no network
- [ ] README limitations + curl examples work as written

## 12. Uniqueness / Anti-Clone Constraints
This is not a generic "chat with your PDF" clone. Municipal-records terminology (agenda, motion, ordinance, roll-call vote, public comment) must appear in fixtures, UI copy, and schemas. Sentence-level citation provenance and the abstain-over-hallucinate policy are mandatory, rendered as citation chips — not bare markdown links. The stub LLM must be visibly labeled in the UI and README. No "upload a resume" framing, no generic chatbot shell, no placeholder-only pages.
