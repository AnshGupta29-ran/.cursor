"""Real-inference smoke test with a checked-in fixture image. Marked `slow`.

Asserts on structure and invariants (5 labels, descending confidences,
sum ≈ 1) — never exact label strings — to stay robust across torch builds.
Run with:  pytest -m slow
"""
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app

from .conftest import make_settings

FIXTURE = Path(__file__).parent / "fixtures" / "laptop.jpg"


@pytest.fixture(scope="module")
def fixture_image():
    """Checked-in photo-realistic fixture (ImageNet-style content)."""
    assert FIXTURE.exists(), f"fixture missing: {FIXTURE}"
    return FIXTURE.read_bytes()


@pytest.mark.slow
def test_real_model_smoke(tmp_path, fixture_image):
    settings = make_settings(tmp_path)
    app = create_app(settings=settings)  # loads real MobileNetV3-Small
    client = TestClient(app)

    info = client.get("/v1/model/info").json()
    assert info["model_loaded"] is True
    assert info["weights_enum"] == "MobileNet_V3_Small_Weights.IMAGENET1K_V1"

    resp = client.post("/v1/predictions", files={"file": ("intake_fixture.png", fixture_image)})
    assert resp.status_code == 200
    body = resp.json()

    top5 = body["top5"]
    assert len(top5) == 5
    confidences = [t["confidence"] for t in top5]
    assert confidences == sorted(confidences, reverse=True)
    assert sum(confidences) == pytest.approx(1.0, abs=0.1)
    assert all(t["mapped_category"] for t in top5)
    assert body["status"] in ("auto_routed", "needs_review")
    assert body["latency_ms"] < 60000  # generous CPU bound (cold-start first inference)
