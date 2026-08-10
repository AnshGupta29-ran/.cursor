"""Core prediction workflow: validate → store asset → infer → map → profile → persist."""
from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

from .classifier import (
    FakeClassifier, ImageClassifier, InferenceError, ModelInfo, TorchvisionClassifier,
)
from .config import Settings
from .db import InputAsset, Prediction, PredictionLabel, ReviewTask
from .errors import ApiError
from .logging_config import get_logger
from .mapping import CategoryMap
from .profiles import ThresholdProfile
from .validation import validate_image_bytes

logger = get_logger()

SAFE_FILENAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")


def sanitize_filename(name: str | None) -> str | None:
    if not name:
        return None
    base = os.path.basename(name)
    return "".join(c if c in SAFE_FILENAME_CHARS else "_" for c in base)[:200]


class PredictionService:
    def __init__(
        self,
        settings: Settings,
        classifier: ImageClassifier,
        category_map: CategoryMap,
        profiles: dict[str, ThresholdProfile],
        session_factory,
    ):
        self.settings = settings
        self.classifier = classifier
        self.category_map = category_map
        self.profiles = profiles
        self.session_factory = session_factory

    # ------------------------------------------------------------ helpers

    def model_info(self) -> ModelInfo:
        return self.classifier.info()

    def get_profile(self, name: str) -> ThresholdProfile:
        profile = self.profiles.get(name)
        if profile is None:
            raise ApiError(
                422,
                "unknown_profile",
                f"Unknown profile {name!r}. Valid profiles: {sorted(self.profiles)}",
            )
        return profile

    def _get_or_create_asset(self, session, data: bytes, content_type: str,
                             width: int, height: int, filename: str | None,
                             store_image: bool) -> InputAsset:
        """Assets are deduped by SHA-256: identical bytes reuse the existing row."""
        sha = hashlib.sha256(data).hexdigest()
        asset = session.query(InputAsset).filter_by(sha256=sha).first()
        if asset is not None:
            return asset

        stored_path = None
        if store_image:
            assets_dir = Path(self.settings.assets_dir)
            assets_dir.mkdir(parents=True, exist_ok=True)
            stored_path = str(assets_dir / f"{sha}.bin")
            with open(stored_path, "wb") as f:
                f.write(data)

        asset = InputAsset(
            sha256=sha,
            original_filename=sanitize_filename(filename),
            content_type=content_type,
            width=width,
            height=height,
            byte_size=len(data),
            stored_path=stored_path,
        )
        session.add(asset)
        session.flush()
        return asset

    # ------------------------------------------------------------ main flow

    def run_prediction(
        self,
        data: bytes,
        filename: str | None,
        profile_name: str,
        intake_tag: str | None,
        store_image: bool | None,
        request_id: str,
    ) -> Prediction:
        """Full single-image intake. Raises ApiError on validation/model failure."""
        profile = self.get_profile(profile_name)
        do_store = self.settings.store_images if store_image is None else store_image

        content_type, width, height = validate_image_bytes(
            data, self.settings.max_upload_bytes, self.settings.min_image_dimension
        )

        if not self.classifier.info().loaded:
            raise ApiError(
                503, "model_unavailable",
                "Model failed to load at startup; inference is unavailable.",
                headers={"Retry-After": "30"},
            )

        start = time.perf_counter()
        try:
            top5 = self.classifier.predict_top5(data)
        except InferenceError as exc:
            logger.error(
                "prediction failed",
                extra={"request_id": request_id, "endpoint": "/v1/predictions",
                       "outcome": "inference_error", "error": str(exc)},
            )
            raise ApiError(
                503, "inference_error",
                "Model inference failed; the intake record was not created.",
                headers={"Retry-After": "5"},
            ) from exc
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        top1, runner_up = top5[0], top5[1]
        top1_category = self.category_map.category_for(top1.imagenet_label)
        reason = profile.evaluate(top1.confidence, runner_up.confidence)

        if reason is None:
            status = "auto_routed"
            routing_hint = self.category_map.routing_for(top1_category)
        else:
            status = "needs_review"
            routing_hint = profile.default_routing

        info = self.classifier.info()
        prediction = Prediction(
            request_id=request_id,
            intake_tag=intake_tag,
            profile_name=profile.name,
            model_name=info.model_name,
            model_version=info.model_version,
            category_map_version=self.category_map.version,
            top1_label=top1.imagenet_label,
            top1_score=top1.confidence,
            top1_category=top1_category,
            latency_ms=latency_ms,
            status=status,
            routing_hint=routing_hint,
        )

        session = self.session_factory()
        try:
            asset = self._get_or_create_asset(
                session, data, content_type, width, height, filename, do_store
            )
            prediction.asset_id = asset.id
            prediction.labels = [
                PredictionLabel(
                    rank=rank,
                    imagenet_label=p.imagenet_label,
                    confidence=p.confidence,
                    mapped_category=self.category_map.category_for(p.imagenet_label),
                )
                for rank, p in enumerate(top5, start=1)
            ]
            session.add(prediction)
            session.flush()

            if reason is not None:
                session.add(ReviewTask(prediction_id=prediction.id, reason=reason))

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        logger.info(
            "prediction completed",
            extra={
                "request_id": request_id,
                "endpoint": "/v1/predictions",
                "sha256": asset.sha256,
                "model_version": prediction.model_version,
                "category_map_version": prediction.category_map_version,
                "profile": profile.name,
                "latency_ms": latency_ms,
                "outcome": status,
            },
        )
        return prediction


def build_default_classifier(settings: Settings) -> ImageClassifier:
    """Production startup path. FakeClassifier is never constructed here."""
    return TorchvisionClassifier(
        settings.model_name, settings.weights_enum, settings.torch_num_threads
    )


class UnavailableClassifier:
    """Stand-in when model load fails at startup: fail fast on requests,
    report model_loaded=false via /health."""

    def __init__(self, model_name: str, weights_enum: str, error: str):
        self._model_name = model_name
        self._weights_enum = weights_enum
        self.error = error

    def info(self) -> ModelInfo:
        return ModelInfo(
            model_name=self._model_name,
            weights_enum=self._weights_enum,
            model_version="unloaded",
            device="cpu",
            loaded=False,
        )

    def predict_top5(self, image_bytes: bytes):
        raise ModelUnavailableError(f"Model not loaded: {self.error}")
