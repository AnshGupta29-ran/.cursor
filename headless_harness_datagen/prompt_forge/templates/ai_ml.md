# Category template: AI / ML Application Platforms

Family shape for products where model inference or ML analysis is the core value —
not a CRUD app with an “AI” label stuck on.

## Product family intent

Users submit inputs (documents, images, text, datasets), the system runs a model or
deterministic ML pipeline, and returns structured, actionable outputs in a UI and/or API.
The product must make evaluation, confidence, and failure modes visible.

## Identity & positioning (invent uniquely)

- Product name and vertical (HR screening, quality inspection, support triage, education)
- Input modality and output artifact (scores, labels, extractions fields, rankings)
- Human-in-the-loop stance (auto-apply vs review queue)
- One twist (compare-against-reference, batch jobs, explainability panel, threshold policies)

## Required capability areas

### Ingestion
- Upload or paste inputs with validation
- Supported formats explicitly listed
- Rejection path for unsupported/corrupt inputs

### Inference / analysis
- Clear model/pipeline choice (pretrained library allowed; document it)
- Structured response schema (top-k labels, fields, similarities, etc.)
- Latency expectations for local demo (synchronous OK if stated)

### Interpretation UX
- Confidence/score presentation
- Highlighted evidence or key features when possible
- History of past analyses for the user

### Evaluation helpers (pick what fits)
- Side-by-side comparison against a reference (job description, gold label, template)
- Threshold configuration or preset profiles
- Export of results (JSON/CSV)

### API surface
- Documented inference endpoint(s)
- Auth if multi-user
- Request logging for auditability

## UX expectations

- Guided first-run sample input
- Loading/progress states during inference
- Error states that distinguish validation vs model failures
- Results that a non-ML engineer can understand

## Data & persistence

Entities may include: User, AnalysisJob, InputAsset, ModelPrediction, FeedbackLabel (optional).
Prefer local model weights or lightweight stubs — prefer real local inference when feasible;
if stubbing, label clearly and still return structured outputs.
Never require downloading torch/cuda or ImageNet weights during the agent run if a stub
or already-cached model can satisfy acceptance; document how to enable the full model later.

## Quality & reliability

- Input validation tests
- Fast endpoint tests with fixture inputs (smoke only during agent runs)
- Deterministic fixtures where possible for CI
- No crashing on empty/partial files
- Slow / GPU / download-heavy tests are optional and must not block VERDICT: PASS

## Documentation & deliverables

- README: model source, install notes, sample curl/UI path
- Limitations section (bias, unsupported languages/formats)
- Reproducibility notes

## Constraints & non-goals

- Not a full MLOps platform unless seed is devops/mlflow-like
- Not training huge models from scratch in-harness
- Avoid “ChatGPT wrapper” with no domain schema

## Acceptance criteria checklist (customize)

- [ ] User can submit a valid input and receive structured predictions
- [ ] Invalid inputs fail clearly
- [ ] Results include confidence or ranked alternatives as specified
- [ ] At least one comparison/evaluation feature works if required by seed
- [ ] API docs or README examples succeed locally
- [ ] Automated tests cover inference endpoint happy path
- [ ] Limitations are documented

## Variation axes

Modality · vertical · batch vs interactive · explainability depth · human review ·
offline model vs API model · multi-class vs extraction

## Anti-clone rules

Do not emit the same “upload resume, show matching %” paragraph set every time.
Change vertical language, schemas, and review workflows to diversify traces.
