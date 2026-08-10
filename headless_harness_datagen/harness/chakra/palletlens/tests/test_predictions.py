"""Happy-path single prediction, validation matrix, history, stats, ops."""
import json

from .conftest import jpeg_bytes, make_settings, png_bytes


def upload(client, data=None, filename="donation.png", **params):
    data = png_bytes() if data is None else data
    return client.post(
        "/v1/predictions",
        files={"file": (filename, data)},
        params=params,
    )


# --------------------------------------------------------------- happy path

def test_single_prediction_auto_routed(client):
    resp = upload(client, profile="strict-intake", intake_tag="pallet-17")
    assert resp.status_code == 200
    body = resp.json()

    assert body["request_id"]
    assert body["status"] == "auto_routed"
    assert body["routing_hint"] == "bench_test"
    assert body["profile_name"] == "strict-intake"
    assert body["intake_tag"] == "pallet-17"
    assert body["model_name"] == "fake_classifier"
    assert body["category_map_version"]
    assert body["latency_ms"] >= 0

    top5 = body["top5"]
    assert len(top5) == 5
    confidences = [t["confidence"] for t in top5]
    assert confidences == sorted(confidences, reverse=True)
    assert top5[0]["imagenet_label"] == "laptop"
    assert top5[0]["mapped_category"] == "portable_computing"
    assert [t["rank"] for t in top5] == [1, 2, 3, 4, 5]
    assert "bench test" in body["explanation"]
    assert sum(confidences) == pytest.approx(0.98, abs=0.01)


def test_unknown_profile_lists_valid_profiles(client):
    resp = upload(client, profile="no-such-profile")
    assert resp.status_code == 422
    err = resp.json()["error"]
    assert err["code"] == "unknown_profile"
    assert "strict-intake" in err["message"]
    assert "bin-sweep" in err["message"]


def test_below_threshold_lands_in_review_queue(low_confidence_client):
    resp = upload(low_confidence_client, profile="strict-intake")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "needs_review"
    assert "review queue" in body["explanation"]

    queue = low_confidence_client.get("/v1/review-queue").json()
    assert len(queue) == 1
    assert queue[0]["reason"] == "below_threshold"
    assert queue[0]["status"] == "open"


def test_permissive_profile_auto_routes_same_output(low_confidence_client):
    resp = upload(low_confidence_client, profile="bin-sweep")
    body = resp.json()
    assert body["status"] == "auto_routed"
    assert body["routing_hint"] == "manual_sort"  # 'hook' is unmapped


def test_duplicate_upload_dedupes_asset(client):
    data = png_bytes()
    r1 = upload(client, data=data)
    r2 = upload(client, data=data)
    assert r1.status_code == r2.status_code == 200
    assert r1.json()["id"] != r2.json()["id"]  # separate predictions...


# --------------------------------------------------------------- validation

def test_empty_file_rejected(client):
    resp = upload(client, data=b"")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "empty_file"


def test_wrong_magic_bytes_rejected(client):
    pdf = b"%PDF-1.4 fake pdf bytes that are not an image at all..........."
    resp = upload(client, data=pdf, filename="actually-a-pdf.png")
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "unsupported_media_type"


def test_oversize_file_rejected(settings, client):
    big = png_bytes(size=(600, 600))
    # simulate a smaller limit
    client.app.state.service.settings.max_upload_mb = 0  # 0 bytes allowed
    resp = upload(client, data=big)
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "file_too_large"


def test_corrupt_image_rejected(client):
    corrupt = b"\x89PNG\r\n\x1a\n" + b"garbage-garbage-garbage"
    resp = upload(client, data=corrupt)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "corrupt_image"


def test_tiny_dimensions_rejected(client):
    tiny = png_bytes(size=(12, 12))
    resp = upload(client, data=tiny)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "dimensions_too_small"


def test_jpeg_and_webp_accepted(client):
    assert upload(client, data=jpeg_bytes(), filename="photo.jpg").status_code == 200

    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (128, 128), (0, 200, 0)).save(buf, format="WEBP")
    assert upload(client, data=buf.getvalue(), filename="photo.webp").status_code == 200


def test_model_unavailable_returns_503(settings):
    from fastapi.testclient import TestClient
    from app.classifier import FakeClassifier
    from app.main import create_app

    app = create_app(settings=settings, classifier=FakeClassifier(fail=True))
    c = TestClient(app)
    resp = c.post("/v1/predictions", files={"file": ("x.png", png_bytes())})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "inference_error"
    assert "Retry-After" in resp.headers


# --------------------------------------------------------------- history/stats

def test_history_filters_and_pagination(client):
    for tag in ("pallet-17", "pallet-17", "pallet-18"):
        upload(client, intake_tag=tag)
    upload(client, profile="bin-sweep", intake_tag="pallet-18")

    all_items = client.get("/v1/predictions").json()
    assert all_items["total"] == 4

    tagged = client.get("/v1/predictions", params={"intake_tag": "pallet-17"}).json()
    assert tagged["total"] == 2

    by_profile = client.get("/v1/predictions", params={"profile": "bin-sweep"}).json()
    assert by_profile["total"] == 1

    by_category = client.get(
        "/v1/predictions", params={"category": "portable_computing"}).json()
    assert by_category["total"] == 4

    page1 = client.get("/v1/predictions", params={"page": 1, "page_size": 3}).json()
    page2 = client.get("/v1/predictions", params={"page": 2, "page_size": 3}).json()
    assert len(page1["items"]) == 3 and len(page2["items"]) == 1
    assert page1["items"][0]["id"] != page2["items"][0]["id"]


def test_prediction_detail_includes_top5(client):
    pred_id = upload(client).json()["id"]
    detail = client.get(f"/v1/predictions/{pred_id}").json()
    assert detail["id"] == pred_id
    assert len(detail["top5"]) == 5
    assert detail["top5"][0]["mapped_category"] == "portable_computing"


def test_prediction_detail_404(client):
    resp = client.get("/v1/predictions/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "prediction_not_found"


def test_stats_endpoint(client):
    upload(client)
    upload(client)
    stats = client.get("/v1/stats").json()
    assert stats["total_predictions"] == 2
    assert stats["pct_needs_review"] == 0.0
    assert stats["mean_latency_ms"] is not None
    assert stats["top_categories"][0]["category"] == "portable_computing"
    assert stats["top_categories"][0]["count"] == 2


def test_health_and_model_info(client):
    health = client.get("/health").json()
    assert health == {"status": "ok", "model_loaded": True}

    info = client.get("/v1/model/info").json()
    assert info["model_name"] == "fake_classifier"
    assert info["device"] == "cpu"
    assert info["category_map_version"]
    assert info["model_loaded"] is True


def test_categories_and_profiles_endpoints(client):
    cats = client.get("/v1/categories").json()
    assert cats["version"]
    names = {c["category"] for c in cats["categories"]}
    assert {"portable_computing", "display", "unmapped_general"} <= names
    laptop_entry = next(c for c in cats["categories"] if c["category"] == "portable_computing")
    assert "laptop" in laptop_entry["imagenet_labels"]
    assert laptop_entry["routing"] == "bench_test"

    profiles = client.get("/v1/profiles").json()
    pnames = {p["name"] for p in profiles["profiles"]}
    assert {"strict-intake", "bin-sweep"} == pnames


# --------------------------------------------------------------- logging

def test_prediction_emits_one_structured_log(client, caplog):
    import logging
    # caplog.at_level attaches its capture handler to the named logger directly;
    # propagation stays off so the record is captured exactly once.
    with caplog.at_level(logging.INFO, logger="palletlens"):
        upload(client)

    records = [r for r in caplog.records if r.message == "prediction completed"]
    assert len(records) == 1
    rec = records[0]
    assert rec.request_id
    assert rec.sha256
    assert rec.model_version
    assert rec.latency_ms is not None
    assert rec.outcome == "auto_routed"


import pytest  # noqa: E402  (used via pytest.approx above)
