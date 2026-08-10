"""Image classification behind an interface so tests can inject a fake.

Real implementation: torchvision pretrained ImageNet model (CPU-only).
Fake implementation: deterministic fixed probability vector, tests only.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Protocol

from PIL import Image, ImageOps


class InferenceError(Exception):
    """Raised when the model itself fails (→ HTTP 503 inference_error)."""


class ModelUnavailableError(Exception):
    """Raised when no model is loaded (→ HTTP 503 model_unavailable)."""


@dataclass(frozen=True)
class ClassPrediction:
    imagenet_label: str
    confidence: float  # rounded to 4 decimals by implementations


@dataclass(frozen=True)
class ModelInfo:
    model_name: str
    weights_enum: str
    model_version: str
    device: str
    loaded: bool


class ImageClassifier(Protocol):
    def info(self) -> ModelInfo: ...
    def predict_top5(self, image_bytes: bytes) -> list[ClassPrediction]: ...


# ---------------------------------------------------------------- real model

_MODEL_REGISTRY = {
    "mobilenet_v3_small": ("mobilenet_v3_small", "MobileNet_V3_Small_Weights"),
    "resnet18": ("resnet18", "ResNet18_Weights"),
}


class TorchvisionClassifier:
    """CPU-only torchvision ImageNet classifier.

    Loads exactly one model at startup; weights enum is pinned by config.
    Inference is serialized via a lock so concurrent requests cannot corrupt
    torch state.
    """

    def __init__(self, model_name: str, weights_enum: str, num_threads: int = 1):
        import threading

        import torch

        torch.set_num_threads(num_threads)
        self._lock = threading.Lock()
        self._device = "cpu"

        if model_name not in _MODEL_REGISTRY:
            raise ValueError(
                f"Unknown MODEL_NAME {model_name!r}. Valid: {sorted(_MODEL_REGISTRY)}"
            )
        fn_name, weights_cls_name = _MODEL_REGISTRY[model_name]

        import torchvision

        weights_cls = getattr(torchvision.models, weights_cls_name)
        try:
            weights = getattr(weights_cls, weights_enum)
        except AttributeError:
            raise ValueError(
                f"Weights enum {weights_enum!r} not found on {weights_cls_name}. "
                f"Valid: {[m.name for m in weights_cls]}"
            )

        self._weights = weights
        self._model = getattr(torchvision.models, fn_name)(weights=weights)
        self._model.eval()
        self._transform = weights.transforms()
        self._categories: list[str] = weights.meta["categories"]
        self._model_name = model_name
        self._weights_enum = f"{weights_cls_name}.{weights_enum}"
        self._torch_version = torch.__version__

    def info(self) -> ModelInfo:
        return ModelInfo(
            model_name=self._model_name,
            weights_enum=self._weights_enum,
            model_version=self._torch_version,
            device=self._device,
            loaded=True,
        )

    def predict_top5(self, image_bytes: bytes) -> list[ClassPrediction]:
        import torch

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img = ImageOps.exif_transpose(img)  # EXIF-orientation normalization
                img = img.convert("RGB")
                tensor = self._transform(img).unsqueeze(0)
        except Exception as exc:  # pragma: no cover - validation catches this earlier
            raise InferenceError(f"Failed to prepare image for inference: {exc}") from exc

        try:
            with self._lock, torch.no_grad():
                logits = self._model(tensor)
                probs = torch.softmax(logits, dim=1)[0]
                top_probs, top_idx = torch.topk(probs, 5)
        except Exception as exc:
            raise InferenceError(f"Model forward pass failed: {exc}") from exc

        return [
            ClassPrediction(
                imagenet_label=self._categories[int(i)],
                confidence=round(float(p), 4),
            )
            for p, i in zip(top_probs.tolist(), top_idx.tolist())
        ]


# ---------------------------------------------------------------- test fake

class FakeClassifier:
    """Deterministic classifier for tests. Never wired into production startup."""

    def __init__(self, predictions: list[ClassPrediction] | None = None, fail: bool = False):
        self._predictions = predictions or [
            ClassPrediction("laptop", 0.62),
            ClassPrediction("desktop_computer", 0.21),
            ClassPrediction("notebook", 0.08),
            ClassPrediction("screen", 0.05),
            ClassPrediction("mouse", 0.02),
        ]
        self._fail = fail

    def info(self) -> ModelInfo:
        return ModelInfo(
            model_name="fake_classifier",
            weights_enum="FAKE_V1",
            model_version="0.0.0-test",
            device="cpu",
            loaded=True,  # `fail` simulates a runtime inference error, not an unloaded model
        )

    def predict_top5(self, image_bytes: bytes) -> list[ClassPrediction]:
        if self._fail:
            raise InferenceError("fake classifier configured to fail")
        return self._predictions
