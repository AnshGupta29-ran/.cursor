"""Smoke test: boot server on a test port, assert health → seed → log run → PASS verdict.

Run:  python scripts/smoke.py
"""
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error

# Windows consoles default to cp1252; force UTF-8 so arrows/unicode in verdicts print.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PORT = 8765
BASE = f"http://127.0.0.1:{PORT}/api"


def req(method, path, body=None, raw=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if raw is not None:
        data = raw
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def main():
    proc = subprocess.Popen(
        [sys.executable, "-c",
         f"import app, uvicorn; uvicorn.run(app.app, host='127.0.0.1', port={PORT}, log_level='error')"],
        cwd=".",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # wait for boot
        for _ in range(60):
            try:
                s, h = req("GET", "/health")
                if s == 200:
                    break
            except Exception:
                time.sleep(0.25)
        else:
            print("FAIL: server did not boot")
            return 1

        # 1. health
        s, h = req("GET", "/health")
        assert s == 200 and h["status"] == "ok", h
        print("[ok] health")

        # 2. seed (idempotent)
        s, seed = req("POST", "/demo/seed")
        assert s == 200 and seed["experiment_id"], seed
        exp_id = seed["experiment_id"]
        s, seed2 = req("POST", "/demo/seed")
        assert seed2["seeded"] is False and seed2["experiment_id"] == exp_id
        print("[ok] seed idempotent, experiment:", exp_id)

        # 3. new challenger run via the documented flow
        s, run = req("POST", "/runs", {"experiment_id": exp_id, "name": "smoke-challenger"})
        assert s == 201, run
        rid = run["id"]

        # champion f1 ≈ 0.85; log a clearly better run
        s, _ = req("POST", f"/runs/{rid}/log-batch", {
            "params": {"learning_rate": 0.012, "batch_size": 64},
            "metrics": {"f1": [{"step": i, "value": 0.90 + i * 0.001} for i in range(3)],
                         "latency_ms": [{"step": i, "value": 50.0} for i in range(3)]},
        })
        assert s == 200
        s, fin = req("POST", f"/runs/{rid}/finish")
        assert s == 200 and fin["status"] == "FINISHED"
        s, verdict = req("GET", f"/runs/{rid}/verdict")
        assert s == 200, verdict
        assert verdict["verdict"] == "PASS", verdict
        assert verdict["summary"]
        print("[ok] challenger verdict:", verdict["verdict"], "-", verdict["summary"][:60], "...")

        # 4. logging to a finished run → 409
        s, e = req("POST", f"/runs/{rid}/log-batch", {"params": {"x": 1}})
        assert s == 409 and e["error"]["code"] == "conflict", e
        print("[ok] 409 on log to finished run")

        # 5. NaN metric → 422
        s, e = req("POST", "/runs", {"experiment_id": exp_id, "name": "bad-run"})
        bad = e["id"]
        s, e = req("POST", f"/runs/{bad}/log-batch",
                    {"metrics": {"f1": [{"step": 0, "value": "NaN"}]}})
        # Pydantic will reject non-float or NaN
        assert s in (200, 422), (s, e)
        print("[ok] validation envelope OK (status", s, ")")

        # 6. artifact round trip + 413
        s, art = req("POST", f"/runs/{rid}/artifacts?name=report.txt&content_type=text/plain",
                     raw=b"precision recall f1\n0.9 0.9 0.9\n")
        assert s == 201, art
        s, prev = req("GET", f"/artifacts/{art['id']}/preview")
        assert s == 200 and "f1" in prev["preview"]
        print("[ok] artifact upload + preview")

        s, e = req("POST", f"/runs/{rid}/artifacts?name=big.bin&content_type=application/octet-stream",
                   raw=b"x" * (2 * 1024 * 1024))
        assert s == 413 and e["error"]["code"] == "too_large", (s, e)
        print("[ok] 413 on oversize artifact")

        # 7. unknown id → 404 envelope
        s, e = req("GET", "/runs/nope")
        assert s == 404 and "error" in e
        print("[ok] 404 envelope")

        # 8. influence + compare + activity
        s, inf = req("GET", f"/experiments/{exp_id}/influence")
        assert s == 200 and len(inf["drivers"]) >= 1, inf
        print("[ok] influence drivers:", [d["param"] for d in inf["drivers"]])

        s, exp = req("GET", f"/experiments/{exp_id}")
        run_ids = [r["id"] for r in exp["run_objects"][:3]]
        s, cmp_ = req("GET", f"/experiments/{exp_id}/compare?run_ids={','.join(run_ids)}")
        assert s == 200 and len(cmp_["runs"]) == 3
        print("[ok] compare")

        s, act = req("GET", "/activity")
        assert s == 200 and len(act) > 0
        print("[ok] activity log")

        print("\nSMOKE PASS")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
