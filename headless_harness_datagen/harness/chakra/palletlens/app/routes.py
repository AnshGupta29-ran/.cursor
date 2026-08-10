"""HTTP routes for PalletLens."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from sqlalchemy import func

from .db import Prediction, ReviewTask
from .errors import ApiError
from .schemas import (
    BatchItemResult, BatchResult, CategoriesOut, CategoryEntry, HealthOut, LabelOut,
    ModelInfoOut, PredictionOut, PredictionPage, PredictionSummary, ProfileOut,
    ProfilesOut, ReviewResolveRequest, ReviewTaskOut, StatsOut,
)
from .service import PredictionService

router = APIRouter()


def get_service(request: Request) -> PredictionService:
    return request.app.state.service


# ------------------------------------------------------------------ formatting

def _explanation(prediction: Prediction) -> str:
    pct = round(prediction.top1_score * 100)
    if prediction.status == "auto_routed":
        return (
            f"Top guess '{prediction.top1_label}' at {pct}% clears the "
            f"{prediction.profile_name} threshold → "
            f"{(prediction.routing_hint or 'manual_sort').replace('_', ' ')}."
        )
    if prediction.status == "needs_review":
        return (
            f"Top guess '{prediction.top1_label}' at {pct}% does not clear the "
            f"{prediction.profile_name} threshold → parked in the review queue "
            f"for a coordinator."
        )
    return f"Prediction failed for '{prediction.top1_label}'."


def _to_summary(p: Prediction) -> PredictionSummary:
    return PredictionSummary(
        id=p.id, request_id=p.request_id, intake_tag=p.intake_tag,
        profile_name=p.profile_name, status=p.status, routing_hint=p.routing_hint,
        top1_label=p.top1_label, top1_score=p.top1_score,
        top1_category=p.top1_category, latency_ms=p.latency_ms, created_at=p.created_at,
    )


def _to_out(p: Prediction) -> PredictionOut:
    return PredictionOut(
        **_to_summary(p).model_dump(),
        model_name=p.model_name, model_version=p.model_version,
        category_map_version=p.category_map_version,
        top5=[
            LabelOut(rank=lbl.rank, imagenet_label=lbl.imagenet_label,
                     confidence=lbl.confidence, mapped_category=lbl.mapped_category)
            for lbl in p.labels
        ],
        explanation=_explanation(p),
    )


def _task_out(t: ReviewTask, include_prediction: bool = False) -> ReviewTaskOut:
    return ReviewTaskOut(
        id=t.id, prediction_id=t.prediction_id, reason=t.reason, status=t.status,
        corrected_label=t.corrected_label, reviewer_note=t.reviewer_note,
        created_at=t.created_at, resolved_at=t.resolved_at,
        prediction=_to_summary(t.prediction) if include_prediction and t.prediction else None,
    )


# ------------------------------------------------------------------ predictions

@router.post(
    "/v1/predictions",
    response_model=PredictionOut,
    summary="Classify one donated item photo",
    description=(
        "Upload a photo from the intake dock. Returns the top-5 ImageNet classes "
        "with refurb-category mappings, a routing hint, and either `auto_routed` "
        "or `needs_review` status per the chosen threshold profile."
    ),
)
async def create_prediction(
    request: Request,
    file: UploadFile,
    profile: str = Query("strict-intake", description="Threshold profile name"),
    intake_tag: str | None = Query(None, description="Pallet/donation tag, e.g. pallet-17"),
    store_image: bool | None = Query(None, description="Override image retention for this request"),
    service: PredictionService = Depends(get_service),
):
    data = await file.read()
    prediction = service.run_prediction(
        data=data,
        filename=file.filename,
        profile_name=profile,
        intake_tag=intake_tag,
        store_image=store_image,
        request_id=request.state.request_id,
    )
    return _to_out(prediction)


@router.post(
    "/v1/predictions:batch",
    response_model=BatchResult,
    summary="Classify a batch of photos (pallet-scale triage)",
    description=(
        "Upload up to 25 photos in one call. Each file is processed independently: "
        "one bad file never sinks the batch. Per-file results carry their own "
        "error object; summary counts are included."
    ),
)
async def create_batch(
    request: Request,
    files: list[UploadFile],
    profile: str = Query("strict-intake"),
    intake_tag: str | None = Query(None),
    service: PredictionService = Depends(get_service),
):
    if not files:
        raise ApiError(422, "empty_batch", "No files were provided.")
    if len(files) > service.settings.batch_max_files:
        raise ApiError(
            422, "batch_too_large",
            f"Batch has {len(files)} files; maximum is {service.settings.batch_max_files}.",
        )

    results: list[BatchItemResult] = []
    summary = {"succeeded": 0, "needs_review": 0, "rejected": 0}

    for f in files:
        data = await f.read()
        try:
            prediction = service.run_prediction(
                data=data, filename=f.filename, profile_name=profile,
                intake_tag=intake_tag, store_image=None,
                request_id=request.state.request_id,
            )
        except ApiError as exc:
            results.append(BatchItemResult(
                filename=f.filename, status="rejected",
                error={"code": exc.code, "message": exc.message},
            ))
            summary["rejected"] += 1
            continue

        results.append(BatchItemResult(
            filename=f.filename, status=prediction.status, prediction=_to_out(prediction),
        ))
        if prediction.status == "needs_review":
            summary["needs_review"] += 1
        else:
            summary["succeeded"] += 1

    return BatchResult(
        request_id=request.state.request_id, results=results, summary=summary,
    )


@router.get(
    "/v1/predictions",
    response_model=PredictionPage,
    summary="Paginated prediction history",
)
def list_predictions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    intake_tag: str | None = None,
    status: str | None = Query(None, description="auto_routed | needs_review | failed"),
    profile: str | None = None,
    category: str | None = Query(None, description="Filter by mapped category"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    service: PredictionService = Depends(get_service),
):
    session = service.session_factory()
    try:
        q = session.query(Prediction)
        if intake_tag:
            q = q.filter(Prediction.intake_tag == intake_tag)
        if status:
            q = q.filter(Prediction.status == status)
        if profile:
            q = q.filter(Prediction.profile_name == profile)
        if category:
            q = q.filter(Prediction.top1_category == category)
        if date_from:
            q = q.filter(Prediction.created_at >= date_from)
        if date_to:
            q = q.filter(Prediction.created_at <= date_to)
        total = q.count()
        items = (
            q.order_by(Prediction.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size).all()
        )
        return PredictionPage(
            items=[_to_summary(p) for p in items],
            total=total, page=page, page_size=page_size,
        )
    finally:
        session.close()


@router.get(
    "/v1/predictions/{prediction_id}",
    response_model=PredictionOut,
    summary="Prediction detail incl. top-5 rows",
)
def get_prediction(prediction_id: str, service: PredictionService = Depends(get_service)):
    session = service.session_factory()
    try:
        p = session.query(Prediction).filter_by(id=prediction_id).first()
        if p is None:
            raise ApiError(404, "prediction_not_found",
                           f"No prediction with id {prediction_id!r}.")
        return _to_out(p)
    finally:
        session.close()


# ------------------------------------------------------------------ review queue

@router.get(
    "/v1/review-queue",
    response_model=list[ReviewTaskOut],
    summary="List open review tasks",
)
def list_review_queue(
    status: str = Query("open", description="open | confirmed | corrected"),
    service: PredictionService = Depends(get_service),
):
    session = service.session_factory()
    try:
        tasks = (
            session.query(ReviewTask).filter_by(status=status)
            .order_by(ReviewTask.created_at.asc()).all()
        )
        return [_task_out(t, include_prediction=True) for t in tasks]
    finally:
        session.close()


@router.get(
    "/v1/review-queue/{task_id}",
    response_model=ReviewTaskOut,
    summary="Fetch one review task",
)
def get_review_task(task_id: int, service: PredictionService = Depends(get_service)):
    session = service.session_factory()
    try:
        t = session.query(ReviewTask).filter_by(id=task_id).first()
        if t is None:
            raise ApiError(404, "review_task_not_found", f"No review task {task_id}.")
        return _task_out(t, include_prediction=True)
    finally:
        session.close()


@router.post(
    "/v1/review-queue/{task_id}/resolve",
    response_model=ReviewTaskOut,
    summary="Resolve a review task (confirmed or corrected)",
)
def resolve_review_task(
    task_id: int,
    body: ReviewResolveRequest,
    service: PredictionService = Depends(get_service),
):
    if body.action not in ("confirmed", "corrected"):
        raise ApiError(422, "invalid_resolution",
                       "action must be 'confirmed' or 'corrected'.")
    session = service.session_factory()
    try:
        t = session.query(ReviewTask).filter_by(id=task_id).first()
        if t is None:
            raise ApiError(404, "review_task_not_found", f"No review task {task_id}.")
        if t.status != "open":
            raise ApiError(409, "review_task_closed",
                           f"Review task {task_id} is already {t.status}.")
        if body.action == "corrected":
            if not body.corrected_label:
                raise ApiError(422, "missing_corrected_label",
                               "corrected_label is required when action='corrected'.")
            if body.corrected_label not in service.category_map.categories:
                raise ApiError(
                    422, "unknown_category",
                    f"Unknown category {body.corrected_label!r}. "
                    f"Valid: {sorted(service.category_map.categories)}",
                )
            t.corrected_label = body.corrected_label
        t.status = body.action
        t.reviewer_note = body.reviewer_note
        t.resolved_at = datetime.now(timezone.utc)
        session.commit()
        return _task_out(t, include_prediction=True)
    finally:
        session.close()


# ------------------------------------------------------------------ reference data

@router.get(
    "/v1/categories",
    response_model=CategoriesOut,
    summary="Category mapping table (labels → categories → routing hints)",
)
def get_categories(service: PredictionService = Depends(get_service)):
    cmap = service.category_map
    by_category: dict[str, list[str]] = {c: [] for c in cmap.categories}
    for label, category in cmap.label_map.items():
        by_category.setdefault(category, []).append(label)
    return CategoriesOut(
        version=cmap.version,
        categories=[
            CategoryEntry(
                category=name,
                routing=cmap.routing_for(name),
                description=(meta or {}).get("description", ""),
                imagenet_labels=sorted(by_category.get(name, [])),
            )
            for name, meta in sorted(cmap.categories.items())
        ],
    )


@router.get("/v1/profiles", response_model=ProfilesOut, summary="Available threshold profiles")
def get_profiles(service: PredictionService = Depends(get_service)):
    return ProfilesOut(profiles=[
        ProfileOut(name=p.name, min_top1_confidence=p.min_top1_confidence,
                   min_margin_over_runner_up=p.min_margin_over_runner_up,
                   default_routing=p.default_routing, description=p.description)
        for p in service.profiles.values()
    ])


# ------------------------------------------------------------------ ops

@router.get("/v1/stats", response_model=StatsOut, summary="Operational summary")
def get_stats(service: PredictionService = Depends(get_service)):
    session = service.session_factory()
    try:
        total = session.query(func.count(Prediction.id)).scalar() or 0
        needs_review = (
            session.query(func.count(Prediction.id))
            .filter(Prediction.status == "needs_review").scalar() or 0
        )
        mean_latency = session.query(func.avg(Prediction.latency_ms)).scalar()
        top_categories = [
            {"category": cat, "count": count}
            for cat, count in (
                session.query(Prediction.top1_category, func.count(Prediction.id))
                .group_by(Prediction.top1_category)
                .order_by(func.count(Prediction.id).desc())
                .limit(10).all()
            )
        ]
        return StatsOut(
            total_predictions=total,
            pct_needs_review=round(100.0 * needs_review / total, 2) if total else 0.0,
            mean_latency_ms=round(mean_latency, 2) if mean_latency is not None else None,
            top_categories=top_categories,
        )
    finally:
        session.close()


@router.get("/v1/model/info", response_model=ModelInfoOut, summary="Model & mapping metadata")
def get_model_info(service: PredictionService = Depends(get_service)):
    info = service.model_info()
    return ModelInfoOut(
        model_name=info.model_name, weights_enum=info.weights_enum,
        model_version=info.model_version, device=info.device,
        category_map_version=service.category_map.version, model_loaded=info.loaded,
    )


@router.get("/health", response_model=HealthOut, summary="Liveness probe", include_in_schema=True)
def health(service: PredictionService = Depends(get_service)):
    return HealthOut(status="ok", model_loaded=service.model_info().loaded)
