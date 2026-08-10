"""Batch partial-failure semantics, review-queue flow, API-key auth."""
import pytest
from fastapi.testclient import TestClient

from app.classifier import ClassPrediction, FakeClassifier
from app.main import create_app

from .conftest import jpeg_bytes, make_settings, png_bytes


def upload(client, data=None, **params):
    data = png_bytes() if data is None else data
    return client.post("/v1/predictions", files={"file": ("donation.png", data)}, params=params)


# --------------------------------------------------------------- batch

def test_batch_mixed_files_partial_failure(client):
    corrupt = b"\x89PNG\r\n\x1a\n" + b"not-really-a-png"
    files = [
        ("files", ("good1.png", png_bytes())),
        ("files", ("good2.jpg", jpeg_bytes())),
        ("files", ("broken.png", corrupt)),
        ("files", ("empty.png", b"")),
        ("files", ("tiny.png", png_bytes(size=(8, 8)))),
    ]
    resp = client.post("/v1/predictions:batch", files=files, params={"intake_tag": "drop-9"})
    assert resp.status_code == 200
    body = resp.json()

    assert body["summary"] == {"succeeded": 2, "needs_review": 0, "rejected": 3}
    assert len(body["results"]) == 5

    statuses = {r["filename"]: r for r in body["results"]}
    assert statuses["good1.png"]["status"] == "auto_routed"
    assert statuses["good1.png"]["prediction"]["top5"][0]["imagenet_label"] == "laptop"
    assert statuses["broken.png"]["error"]["code"] == "corrupt_image"
    assert statuses["empty.png"]["error"]["code"] == "empty_file"
    assert statuses["tiny.png"]["error"]["code"] == "dimensions_too_small"


def test_batch_ten_files(client):
    files = [("files", (f"item-{i}.png", png_bytes(color=(i * 20 % 255, 10, 10))))
             for i in range(10)]
    resp = client.post("/v1/predictions:batch", files=files)
    assert resp.status_code == 200
    assert resp.json()["summary"]["succeeded"] == 10


def test_batch_over_limit_rejected(client):
    files = [("files", (f"i{i}.png", png_bytes())) for i in range(26)]
    resp = client.post("/v1/predictions:batch", files=files)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "batch_too_large"


def test_batch_needs_review_counts(settings):
    low = FakeClassifier([
        ClassPrediction("hook", 0.31), ClassPrediction("clog", 0.20),
        ClassPrediction("mailbox", 0.19), ClassPrediction("hammer", 0.17),
        ClassPrediction("nail", 0.13),
    ])
    app = create_app(settings=settings, classifier=low)
    c = TestClient(app)
    files = [("files", ("a.png", png_bytes())), ("files", ("b.png", jpeg_bytes()))]
    resp = c.post("/v1/predictions:batch", files=files)
    assert resp.json()["summary"] == {"succeeded": 0, "needs_review": 2, "rejected": 0}


# --------------------------------------------------------------- review queue

def test_review_queue_full_flow(low_confidence_client):
    pred = upload(low_confidence_client, profile="strict-intake").json()
    assert pred["status"] == "needs_review"

    queue = low_confidence_client.get("/v1/review-queue").json()
    assert len(queue) == 1
    task = queue[0]
    assert task["reason"] == "below_threshold"
    assert task["prediction"]["id"] == pred["id"]

    detail = low_confidence_client.get(f"/v1/review-queue/{task['id']}").json()
    assert detail["prediction"]["top1_label"] == "hook"

    resolved = low_confidence_client.post(
        f"/v1/review-queue/{task['id']}/resolve",
        json={"action": "corrected", "corrected_label": "peripheral",
              "reviewer_note": "Dock connector, not a hook."},
    )
    assert resolved.status_code == 200
    body = resolved.json()
    assert body["status"] == "corrected"
    assert body["corrected_label"] == "peripheral"
    assert body["resolved_at"] is not None

    # closed tasks leave the open queue
    assert low_confidence_client.get("/v1/review-queue").json() == []
    # and re-resolving is rejected
    again = low_confidence_client.post(
        f"/v1/review-queue/{task['id']}/resolve", json={"action": "confirmed"})
    assert again.status_code == 409


def test_resolve_confirmed(low_confidence_client):
    upload(low_confidence_client, profile="strict-intake")
    task = low_confidence_client.get("/v1/review-queue").json()[0]
    resp = low_confidence_client.post(
        f"/v1/review-queue/{task['id']}/resolve", json={"action": "confirmed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


def test_corrected_requires_known_category(low_confidence_client):
    upload(low_confidence_client, profile="strict-intake")
    task = low_confidence_client.get("/v1/review-queue").json()[0]

    missing = low_confidence_client.post(
        f"/v1/review-queue/{task['id']}/resolve", json={"action": "corrected"})
    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "missing_corrected_label"

    bogus = low_confidence_client.post(
        f"/v1/review-queue/{task['id']}/resolve",
        json={"action": "corrected", "corrected_label": "not_a_category"})
    assert bogus.status_code == 422
    assert bogus.json()["error"]["code"] == "unknown_category"


# --------------------------------------------------------------- auth

def test_api_key_auth(tmp_path):
    settings = make_settings(tmp_path, api_key="secret-coop-key")
    app = create_app(settings=settings, classifier=FakeClassifier())
    c = TestClient(app)

    # /health is always open
    assert c.get("/health").status_code == 200

    # /v1/* requires the key
    no_key = c.get("/v1/profiles")
    assert no_key.status_code == 401
    assert no_key.json()["error"]["code"] == "unauthorized"

    bad_key = c.get("/v1/profiles", headers={"X-API-Key": "wrong"})
    assert bad_key.status_code == 401

    good = c.get("/v1/profiles", headers={"X-API-Key": "secret-coop-key"})
    assert good.status_code == 200


def test_open_mode_when_no_api_key(client):
    assert client.get("/v1/profiles").status_code == 200
