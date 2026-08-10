import io
import os
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.classifier import ClassPrediction, FakeClassifier
from app.config import Settings
from app.main import create_app

BASE_DIR = Path(__file__).resolve().parent.parent


def make_settings(tmp_path, **overrides) -> Settings:
    defaults = dict(
        database_url=f"sqlite:///{tmp_path}/test.db",
        assets_dir=str(tmp_path / "assets"),
        category_map_path=str(BASE_DIR / "category_map.yaml"),
        profiles_path=str(BASE_DIR / "profiles.yaml"),
        store_images=True,
        api_key=None,
    )
    defaults.update(overrides)
    return Settings(**defaults)


def png_bytes(size=(128, 128), color=(200, 30, 30)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def jpeg_bytes(size=(128, 128), color=(30, 30, 200)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture()
def settings(tmp_path):
    return make_settings(tmp_path)


@pytest.fixture()
def client(settings):
    from fastapi.testclient import TestClient
    app = create_app(settings=settings, classifier=FakeClassifier())
    return TestClient(app)


@pytest.fixture()
def low_confidence_classifier():
    return FakeClassifier([
        ClassPrediction("hook", 0.31),
        ClassPrediction("clog", 0.20),
        ClassPrediction("mailbox", 0.19),
        ClassPrediction("hammer", 0.17),
        ClassPrediction("nail", 0.13),
    ])


@pytest.fixture()
def low_confidence_client(settings, low_confidence_classifier):
    from fastapi.testclient import TestClient
    app = create_app(settings=settings, classifier=low_confidence_classifier)
    return TestClient(app)
