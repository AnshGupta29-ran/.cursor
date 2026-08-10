# PLATFORM PROMPT — PalletLens: Intake Triage Vision API for Electronics Refurbishment Co-ops

## 1. Project Request / Product Identity

Build **PalletLens**, a REST API service that helps community electronics-reuse and refurbishment co-ops triage incoming donated hardware. Volunteers photograph each donated item (laptops, monitors, phones, small appliances, mystery cables) at the intake dock; PalletLens runs a **pre-trained PyTorch image classifier** (torchvision ImageNet weights, CPU-only) and returns the **top-5 predicted classes with calibrated confidence scores**, then layers domain logic on top: category hints, routing suggestions (bench-test vs. parts-harvest vs. certified-recycle), confidence-threshold policies, a human review queue for uncertain items, and an audit trail of every prediction.

**Tech stack (locked by seed):** Python 3.11+, FastAPI, PyTorch + torchvision (pretrained ImageNet model — **MobileNetV3-Small** as the default for CPU latency, with a config switch for ResNet-18), Uvicorn, pytest. Persistence via SQLite + SQLAlchemy. Swagger UI (FastAPI's automatic OpenAPI docs) is the primary interactive interface; no custom frontend is required.

**The twist:** PalletLens is not a bare classifier. Raw ImageNet labels are funneled through a **versioned, human-editable category-mapping table** into refurbishment-domain terms, and every prediction is evaluated against a **named threshold profile** that decides whether the item is auto-routed or parked in a **review queue** until a staffer confirms the label.

## 2. Target Users & Primary Jobs-to-Be-Done

- **Intake volunteers (non-technical):** snap a photo of a donated device, upload it, and get an immediate "what is this and where does it go" answer. They never touch code — they use the Swagger UI or a co-op tablet tool that calls the API.
- **Co-op intake coordinators:** define threshold profiles ("strict" for high-value computing gear, "permissive" for cable bins), work the low-confidence review queue, and correct labels so misclassifications are captured as feedback data.
- **Operations / compliance volunteers:** need an auditable log of what was predicted, when, with which model version, and which image (by hash), because donated-asset intake feeds downstream resale and certified-recycling (R2/e-Stewarts-style) reporting.
- **Integrators (co-op IT volunteers):** script batch triage of a whole pallet's photos via the API.

## 3. Core Requirements / Entities

Persist these entities (SQLite, SQLAlchemy models, Alembic or create-all on startup — your choice, documented):

| Entity | Key fields |
|---|---|
| **InputAsset** | id, sha256 hash, original filename, content type, width/height, byte size, stored-path-or-null (retention flag), created_at |
| **Prediction** | id (UUID), asset_id (FK), request_id, intake_tag (client-supplied pallet/donation tag, optional), profile_name, model_name, model_version, top-1 label + score, latency_ms, status (`auto_routed` \| `needs_review` \| `failed`), routing_hint, created_at |
| **PredictionLabel** | prediction_id (FK), rank (1–5), imagenet_label, confidence, mapped_category |
| **ReviewTask** | id, prediction_id (FK), reason (e.g., `below_threshold`, `ambiguous_margin`), status (`open` \| `confirmed` \| `corrected`), corrected_label (nullable), reviewer_note, resolved_at |
| **ThresholdProfile** (config-backed, exposed read-only via API) | name, min_top1_confidence, min_margin_over_runner_up, default_routing |

Structured JSON **request logs** must record every prediction call: request_id, timestamp, endpoint, file hash, model version, latency, outcome. Errors must also be logged.

## 4. Major Feature Areas

### 4.1 Inference service
- Load **one** torchvision pretrained model at startup (default `mobilenet_v3_small`, weights `IMAGENET1K_V1`); the exact weights enum is pinned in config and reported by the API.
- Preprocessing must use the weights' own transform pipeline (`weights.transforms()`), including EXIF-orientation normalization before transforms.
- Return **top-5** labels as softmax probabilities, rounded to 4 decimals, each paired with its ImageNet class name and its **mapped refurb category** (see 4.2).
- Model runs on CPU, synchronously; target < 1.5 s per image on a commodity laptop. Inference must be wrapped so a model-internal failure surfaces as HTTP 503 (`model_unavailable` or `inference_error`), never an unhandled traceback.
- The classifier must be **behind an interface** so tests can inject a deterministic fake (see §9).

### 4.2 Domain mapping & routing (the anti-generic layer)
- Ship a **versioned YAML mapping table** (`category_map.yaml`) translating a curated subset of ImageNet labels into refurb categories, e.g. `laptop → portable_computing`, `monitor → display`, `cellular_telephone → mobile_device`, `microwave → small_appliance`, `mouse → peripheral`. Unmapped labels fall through to category `unmapped_general`.
- Each category has a **default routing hint**: `bench_test`, `parts_harvest`, `certified_recycle`, or `manual_sort`.
- The mapping file version is stamped on every stored Prediction.

### 4.3 Threshold profiles
- Profiles defined in config (YAML or env), e.g.:
  - `strict-intake`: top-1 ≥ 0.45 **and** margin over runner-up ≥ 0.15 → auto-route; else review queue.
  - `bin-sweep`: top-1 ≥ 0.25 → auto-route.
- Clients select a profile per request; unknown profile names → 422 with the list of valid profiles.
- Predictions failing a profile create a **ReviewTask** with a machine-readable reason.

### 4.4 Upload validation
- Accept `image/jpeg`, `image/png`, `image/webp` via **magic-byte sniffing** (not extension or declared content-type alone).
- Enforce: max size (default 10 MB, configurable), min dimensions (e.g., ≥ 64×64), decodable by PIL without exception, EXIF-orientation handled.
- Every rejection is a clean 4xx with a structured error code (`unsupported_media_type`, `file_too_large`, `corrupt_image`, `dimensions_too_small`, `empty_file`) — distinct from 5xx model failures.

### 4.5 Review queue & feedback capture
- List open tasks, fetch one, resolve as `confirmed` (accept top-1) or `corrected` (supply the right category from the known category list).
- Resolutions are stored on the ReviewTask and back-reference the Prediction, forming a future evaluation dataset.

### 4.6 Batch triage
- Multi-file endpoint (up to 25 images per call) for pallet-scale processing. Per-file results with per-file status; one bad file must not sink the batch (partial-failure semantics, each entry carries its own error object). Summary counts included (`succeeded`, `needs_review`, `rejected`).

### 4.7 History, stats & ops
- Paginated prediction history, filterable by intake_tag, status, profile, mapped category, date range.
- Lightweight stats endpoint: total predictions, % needs_review, mean latency, top-10 mapped categories.
- `/health` (liveness, includes model-loaded flag) and `/v1/model/info` (model name, weights enum, version, device, category-map version).

## 5. Domain-Specific Workflows

**Happy path — single intake:**
1. Volunteer uploads `IMG_2041.jpg` with `intake_tag=pallet-17` and `profile=strict-intake` via Swagger UI or curl.
2. API validates bytes, stores the asset (per retention policy), runs inference in ~300 ms, maps top-5 labels, evaluates the profile.
3. Response: request_id, top-5 list (label, confidence, mapped_category), routing hint `bench_test`, status `auto_routed`. Record persisted; structured log line emitted.

**Low-confidence path:** same call on a blurry photo of a dock connector → top-1 = 0.31 → status `needs_review`, ReviewTask created with reason `below_threshold`. Coordinator later lists the queue, views the asset, resolves as `corrected` with category `peripheral`.

**Batch path:** coordinator POSTs 12 photos from one donation drop; response returns 12 per-file results — 9 auto-routed, 2 needs_review, 1 rejected (`corrupt_image`) — plus summary counts.

**Edge cases that must be handled gracefully:** zero-byte file; a `.png` that is actually a PDF; 50 MB file (413/422 per your documented choice); 12×12 pixel image; valid image while model failed to load at startup (503 with `Retry-After` guidance); duplicate upload of the same bytes (same hash — document whether you dedupe the asset row; either is acceptable if consistent); batch of mixed valid/invalid files; unknown profile name; EXIF-rotated portrait photo.

## 6. Data & Persistence Expectations

- SQLite file database, schema created automatically on first run; connection settings via environment.
- **Image retention is configurable:** default `store_images=true` writes originals under a local `assets/` directory (hashed filenames); when `false`, only the SHA-256 hash and metadata are kept — the Prediction record exists either way.
- Config via `pydantic-settings` + env vars: `MODEL_NAME`, `WEIGHTS_ENUM`, `MAX_UPLOAD_MB`, `STORE_IMAGES`, `DATABASE_URL`, `CATEGORY_MAP_PATH`, `PROFILES_PATH`, `API_KEY` (optional — if set, all `/v1/*` endpoints require header `X-API-Key`; if unset, open dev mode, clearly documented).
- No external services; everything runs offline after the one-time weights download (document caching/pre-download for offline demos).

## 7. UX / API Surface Expectations

Primary "UI" is **FastAPI's automatic Swagger at `/docs`** — it must be fully annotated (summary, description, response models, example payloads) so a volunteer can execute the whole intake workflow from the browser.

| Endpoint | Purpose |
|---|---|
| `POST /v1/predictions` | single-image classify (multipart; query: `profile`, `intake_tag`, `store_image`) |
| `POST /v1/predictions:batch` | multi-file classify with partial-failure semantics |
| `GET /v1/predictions` / `GET /v1/predictions/{id}` | paginated history / detail incl. top-5 rows |
| `GET /v1/review-queue` · `POST /v1/review-queue/{id}/resolve` | work the queue |
| `GET /v1/categories` | mapping table (labels → categories → routing hints) + version |
| `GET /v1/profiles` | available threshold profiles |
| `GET /v1/stats` | operational summary |
| `GET /health` · `GET /v1/model/info` | ops |

- Consistent error envelope: `{"error": {"code": "...", "message": "...", "request_id": "..."}}`.
- Loading/latency honesty: responses include `latency_ms`; README states synchronous CPU inference expectations.
- Results must be legible to a non-ML person: mapped category and routing hint displayed alongside raw ImageNet jargon, with a one-line `explanation` field (e.g., *"Top guess 'laptop' at 62% clears the strict-intake threshold → bench test."*).

## 8. Quality, Security, and Reliability Expectations

- No crashes on empty, partial, corrupt, or adversarial files; decompression-bomb guard via PIL limits (`Image.MAX_IMAGE_PIXELS`).
- Filenames sanitized; stored assets keyed by hash, never by client filename.
- Inference concurrency documented (torch thread settings); a second request during inference must not corrupt state.
- Weights are pinned; model load failure at startup fails fast with a clear log, and `/health` reports `model_loaded: false`.
- Optional API-key auth (constant-time compare); prediction logs contain no raw image bytes, only hashes.
- Deterministic behavior for CI: the fake classifier returns fixed probability vectors; real-model tests use a checked-in fixture image and assert on **structure and invariants** (5 labels, descending confidences, sums ≈ 1), not exact label strings, to stay robust across torch builds.

## 9. Documentation & Testing Expectations

**README must include:** model source and license (torchvision ImageNet weights), one-time weights-download note, quickstart (`pip install -r requirements.txt`, `uvicorn ...`), a working curl example for single + batch prediction, Swagger path, configuration table, the category-map format, and a **Limitations** section (ImageNet domain gap for damaged/disassembled gear, class bias, English labels only, CPU latency, not a certified-grading tool).

**Tests (pytest + FastAPI TestClient/httpx), all must pass:**
- Happy-path single prediction via injected fake classifier (deterministic top-5, schema, profile evaluation, routing hint).
- Validation: wrong magic bytes, oversize, corrupt bytes, tiny dimensions, empty file → correct error codes.
- Batch: mixed valid/invalid files → partial results + summary counts.
- Review queue: low-confidence fake output creates a task; resolve as `corrected`; task closes; corrected label persisted.
- History filters and pagination; stats endpoint shape; `/health` and `/v1/model/info`.
- Logging: a prediction emits exactly one structured log record containing request_id, hash, model version, latency.
- One real-inference smoke test with a checked-in fixture image, marked `slow` (skippable in CI).
- Optional-auth test: with `API_KEY` set, missing key → 401, correct key → 200.

## 10. Constraints & Non-Goals

- **No model training or fine-tuning** — pretrained weights only. **No GPU required.**
- Not an MLOps platform: no experiment tracking, drift dashboards, or model registry.
- No user accounts/roles beyond the optional single API key; no multi-tenancy.
- No custom web frontend — Swagger UI plus clean JSON is the product surface.
- No cloud storage, message queues, or background workers; synchronous is the documented design.
- The fake/stub classifier exists **only** for tests and must never serve production requests.

## 11. Acceptance Criteria (Checkable)

- [ ] `POST /v1/predictions` with a valid JPEG/PNG/WebP returns top-5 classes with descending confidence scores, mapped categories, routing hint, and request_id.
- [ ] Invalid inputs (wrong type, corrupt, oversize, undersize, empty) each fail with a distinct documented 4xx error code; model failures return 503 — no tracebacks leak.
- [ ] Swagger UI at `/docs` documents every endpoint and can execute the full intake workflow.
- [ ] Every prediction is persisted (with top-5 rows, model version, profile, latency) and emits one structured log line; history and stats endpoints reflect it.
- [ ] At least two threshold profiles work; a below-threshold prediction lands in the review queue and can be resolved as confirmed or corrected via API.
- [ ] Batch endpoint handles ≥ 10 mixed files with correct partial-failure semantics and summary counts.
- [ ] Category mapping table is loaded from a versioned file and its version appears on predictions and in `/v1/categories`.
- [ ] `pytest` passes: endpoint happy path, validation matrix, review flow, batch, logging assertion, plus a `slow` real-model smoke test.
- [ ] README quickstart and curl examples run verbatim on a fresh checkout; Limitations section exists.

## 12. Uniqueness / Anti-Clone Constraints for This Run

- This is **PalletLens**, a refurbishment-intake triage tool — not a generic "image classifier demo." All API copy, field names, examples, and README language must use domain-authentic vocabulary: *intake tag, pallet, bench test, parts harvest, certified recycle, review queue, threshold profile*. No lorem-ipsum, no "your image is a cat 🐱" sample copy.
- The **top-5 + category mapping + threshold profile + review queue** combination is mandatory; an endpoint that merely returns raw ImageNet labels is a failing submission.
- Do not hardcode prediction responses in the API layer; deterministic behavior belongs only in the injected test double.
- Error codes must be the named enumeration from §4.4/§7, not bare FastAPI defaults.
- Do not rename the stack (FastAPI + PyTorch/torchvision + SQLite + pytest) and do not substitute a hosted vision API — inference is local and pretrained.
- at end it should run on my browser without any hard installation requirements. 