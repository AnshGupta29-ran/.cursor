"""Pydantic response models — the Swagger-visible API contract."""
from datetime import datetime

from pydantic import BaseModel, Field


class LabelOut(BaseModel):
    rank: int = Field(..., examples=[1])
    imagenet_label: str = Field(..., examples=["laptop"])
    confidence: float = Field(..., examples=[0.62])
    mapped_category: str = Field(..., examples=["portable_computing"])


class PredictionOut(BaseModel):
    id: str = Field(..., examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    request_id: str
    intake_tag: str | None = Field(None, examples=["pallet-17"])
    profile_name: str = Field(..., examples=["strict-intake"])
    model_name: str
    model_version: str
    category_map_version: str
    status: str = Field(..., examples=["auto_routed"])
    routing_hint: str | None = Field(None, examples=["bench_test"])
    top1_label: str
    top1_score: float
    top1_category: str
    latency_ms: float
    created_at: datetime
    top5: list[LabelOut]
    explanation: str = Field(
        ..., examples=["Top guess 'laptop' at 62% clears the strict-intake threshold → bench test."]
    )


class PredictionSummary(BaseModel):
    id: str
    request_id: str
    intake_tag: str | None
    profile_name: str
    status: str
    routing_hint: str | None
    top1_label: str
    top1_score: float
    top1_category: str
    latency_ms: float
    created_at: datetime


class PredictionPage(BaseModel):
    items: list[PredictionSummary]
    total: int
    page: int
    page_size: int


class ReviewTaskOut(BaseModel):
    id: int
    prediction_id: str
    reason: str = Field(..., examples=["below_threshold"])
    status: str = Field(..., examples=["open"])
    corrected_label: str | None
    reviewer_note: str | None
    created_at: datetime
    resolved_at: datetime | None
    prediction: PredictionSummary | None = None


class ReviewResolveRequest(BaseModel):
    action: str = Field(..., examples=["corrected"], description="'confirmed' (accept top-1) or 'corrected' (supply the right category).")
    corrected_label: str | None = Field(None, examples=["peripheral"])
    reviewer_note: str | None = None


class CategoryEntry(BaseModel):
    category: str
    routing: str
    description: str
    imagenet_labels: list[str]


class CategoriesOut(BaseModel):
    version: str
    categories: list[CategoryEntry]


class ProfileOut(BaseModel):
    name: str
    min_top1_confidence: float
    min_margin_over_runner_up: float
    default_routing: str
    description: str


class ProfilesOut(BaseModel):
    profiles: list[ProfileOut]


class StatsOut(BaseModel):
    total_predictions: int
    pct_needs_review: float
    mean_latency_ms: float | None
    top_categories: list[dict] = Field(..., examples=[[{"category": "portable_computing", "count": 12}]])


class HealthOut(BaseModel):
    status: str = Field(..., examples=["ok"])
    model_loaded: bool


class ModelInfoOut(BaseModel):
    model_name: str
    weights_enum: str
    model_version: str
    device: str
    category_map_version: str
    model_loaded: bool


class BatchItemResult(BaseModel):
    filename: str | None
    status: str = Field(..., examples=["auto_routed"], description="auto_routed | needs_review | rejected | failed")
    prediction: PredictionOut | None = None
    error: dict | None = Field(None, examples=[{"code": "corrupt_image", "message": "..."}])


class BatchResult(BaseModel):
    request_id: str
    results: list[BatchItemResult]
    summary: dict = Field(..., examples=[{"succeeded": 9, "needs_review": 2, "rejected": 1}])
