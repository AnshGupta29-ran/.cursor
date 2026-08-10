# PalletLens

**Intake triage vision API for electronics-reuse and refurbishment co-ops.**

Volunteers photograph donated hardware at the intake dock (laptops, monitors,
phones, small appliances, mystery cables). PalletLens runs a pretrained
torchvision ImageNet classifier **locally on CPU**, returns the **top-5 classes
with confidence scores**, and layers refurbishment-domain logic on top:

- a **versioned, human-editable category map** turns raw ImageNet jargon into
  refurb terms (`laptop → portable_computing`),
- named **threshold profiles** decide whether an item is **auto-routed**
  (`bench_test` / `parts_harvest` / `certified_recycle` / `manual_sort`) or
  parked in a **review queue** for a coordinator,
- every prediction is persisted (model version, category-map version, latency,
  image SHA-256) and emitted as one structured JSON log line for audit.

The interactive interface is FastAPI's automatic **Swagger UI at `/docs`** —
no custom frontend.

---

## Quickstart

Requires Python 3.11+ and pip. Everything runs locally; the only download is a
one-time ~10 MB weights fetch on first start.

```bash
cd palletlens

# 1. CPU-only torch (small wheel, no CUDA)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 2. everything else
pip install -r requirements.txt

# 3. run
python run.py        # or: uvicorn app.main:app --port 8000
```

Open **http://127.0.0.1:8000/docs** in your browser — you can execute the
entire intake workflow (upload → review queue → resolve) from Swagger.

**Offline demos:** run the server once while online so torchvision caches the
weights (`~/.cache/torch/hub/checkpoints/`). After that, no network is needed.

## curl examples

Single intake (profile + pallet tag):

```bash
curl -X POST "http://127.0.0.1:8000/v1/predictions?profile=strict-intake&intake_tag=pallet-17" \
  -F "file=@IMG_2041.jpg"
```

Response (abridged):

```json
{
  "id": "3fa85f64-…",
  "request_id": "c2f1…",
  "status": "auto_routed",
  "routing_hint": "bench_test",
  "top1_label": "laptop",
  "top1_score": 0.62,
  "latency_ms": 312.4,
  "top5": [
    {"rank": 1, "imagenet_label": "laptop", "confidence": 0.62, "mapped_category": "portable_computing"},
    …
  ],
  "explanation": "Top guess 'laptop' at 62% clears the strict-intake threshold → bench test."
}
```

Batch triage (one bad file never sinks the batch):

```bash
curl -X POST "http://127.0.0.1:8000/v1/predictions:batch?intake_tag=drop-9" \
  -F "files=@a.jpg" -F "files=@b.png" -F "files=@c.webp"
```

Work the review queue:

```bash
curl "http://127.0.0.1:8000/v1/review-queue"
curl -X POST "http://127.0.0.1:8000/v1/review-queue/1/resolve" \
  -H "Content-Type: application/json" \
  -d '{"action": "corrected", "corrected_label": "peripheral", "reviewer_note": "Dock connector."}'
```

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `MODEL_NAME` | `mobilenet_v3_small` | `mobilenet_v3_small` or `resnet18` |
| `WEIGHTS_ENUM` | `IMAGENET1K_V1` | Pinned torchvision weights enum |
| `MAX_UPLOAD_MB` | `10` | Max upload size (→ `413 file_too_large`) |
| `STORE_IMAGES` | `true` | Keep originals under `assets/` (hashed filenames); `false` keeps hash+metadata only |
| `DATABASE_URL` | `sqlite:///palletlens.db` | SQLAlchemy URL; schema auto-created on startup |
| `CATEGORY_MAP_PATH` | `category_map.yaml` | Versioned label→category mapping table |
| `PROFILES_PATH` | `profiles.yaml` | Threshold profiles |
| `API_KEY` | *(unset)* | If set, all `/v1/*` endpoints require header `X-API-Key` (constant-time compare). Unset = open dev mode |
| `TORCH_NUM_THREADS` | `1` | Torch CPU threads; inference is serialized behind a lock |

## Category map format

`category_map.yaml` — bump `version` on every edit; the version is stamped on
each stored Prediction and reported by `GET /v1/categories`:

```yaml
version: "2026.07.1"
categories:
  portable_computing: {routing: bench_test, description: "…"}
label_map:
  laptop: portable_computing
  monitor: display
```

Unmapped labels fall through to `unmapped_general` (routing `manual_sort`).

## Threshold profiles

```yaml
profiles:
  strict-intake:  {min_top1_confidence: 0.45, min_margin_over_runner_up: 0.15, default_routing: bench_test}
  bin-sweep:      {min_top1_confidence: 0.25, min_margin_over_runner_up: 0.0,  default_routing: manual_sort}
```

Failing predictions create a `ReviewTask` with reason `below_threshold` or
`ambiguous_margin`. Unknown profile names → `422 unknown_profile` with the
valid list.

## Error envelope & codes

All errors share `{"error": {"code", "message", "request_id"}}`.

| Code | HTTP | Trigger |
|---|---|---|
| `empty_file` | 422 | zero-byte upload |
| `unsupported_media_type` | 415 | magic bytes not JPEG/PNG/WebP (declared content-type is ignored) |
| `file_too_large` | 413 | over `MAX_UPLOAD_MB` |
| `corrupt_image` | 422 | PIL cannot decode |
| `dimensions_too_small` | 422 | under 64×64 |
| `unknown_profile` | 422 | profile name not in `profiles.yaml` |
| `model_unavailable` / `inference_error` | 503 | model not loaded / forward pass failed (includes `Retry-After`) |

## Model source & license

Default model: **MobileNetV3-Small** with torchvision `IMAGENET1K_V1` weights
(ImageNet-1k, 1000 classes). Weights are downloaded once from
download.pytorch.org and governed by the
[torchvision license (BSD-3)](https://github.com/pytorch/vision); ImageNet
data terms apply to the labels. Inference is synchronous, CPU-only, and
serialized; expect ~0.3–1.5 s per image on a commodity laptop. Each response
carries `latency_ms` so clients see real timings.

## Persistence & audit

SQLite via SQLAlchemy, schema auto-created on first run. `InputAsset` rows are
**deduped by SHA-256** (re-uploading identical bytes reuses the asset row but
creates a new Prediction). Stored assets use hashed filenames under `assets/`;
client filenames are sanitized and never used as storage keys. Request logs
contain hashes and metadata only — never image bytes.

## Tests

```bash
pytest              # full suite minus the real-model smoke test
pytest -m slow      # real MobileNetV3-Small inference on a fixture image
```

Tests inject a deterministic `FakeClassifier` behind the same interface as the
real model; the fake is never wired into production startup.

## Limitations

- **Domain gap:** ImageNet covers intact consumer objects. Damaged,
  disassembled, or part-donor gear (cracked boards, loose cables) is often
  misclassified — that's what the review queue is for.
- **Class bias:** top-1 favors common ImageNet classes; treat confidence as a
  triage signal, not a grade.
- **English ImageNet labels only** in raw output; refurb categories are the
  human-facing terms.
- **CPU latency:** synchronous, ~0.3–1.5 s/image. Not designed for
  high-throughput video.
- **Not a certified-grading tool:** PalletLens suggests routing; R2/e-Stewards
  grading and data-wipe certification remain human processes.
