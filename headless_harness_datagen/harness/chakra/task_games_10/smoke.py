#!/usr/bin/env python3
"""Smoke: start SeedStreet, buy→advance→sell→settle twice, assert identical profit."""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"


def http(method: str, path: str, data: dict | None = None) -> tuple[int, str]:
    body = None
    headers = {}
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def wait_up(timeout: float = 8.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            code, page = http("GET", "/")
            if code == 200 and "SeedStreet" in page:
                return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("server did not start")


def one_flow(handle: str) -> str:
    code, _ = http("POST", "/run/new", {"handle": handle, "seed": "7"})
    assert code in (200, 303), code
    # follow by scanning leaderboard / opening latest — parse Location via opener
    # urllib follows redirects for POST→GET sometimes; fetch home then last run via tape links.
    # Simpler: create via internal API by posting and reading redirect manually.
    return handle


def flow_profit(handle: str) -> int:
    """Drive a full flow using cookie-less redirects with urlopen redirect disabled."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
            return None

    opener = urllib.request.build_opener(NoRedirect)

    def post(path: str, data: dict) -> str:
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(
            BASE + path, data=body, method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            opener.open(req, timeout=5)
            raise AssertionError("expected redirect")
        except urllib.error.HTTPError as e:
            assert e.code in (302, 303), e.code
            loc = e.headers.get("Location")
            assert loc, "missing Location"
            return loc

    loc = post("/run/new", {"handle": handle, "seed": "7"})
    run_path = urllib.parse.urlparse(loc).path  # /run/N
    run_id = run_path.strip("/").split("/")[-1]
    post(f"/run/{run_id}/trade", {"symbol": "KELP", "side": "buy", "qty": "40"})
    post(f"/run/{run_id}/advance", {"steps": "10"})
    post(f"/run/{run_id}/trade", {"symbol": "KELP", "side": "sell", "qty": "20"})
    post(f"/run/{run_id}/advance", {"steps": "999"})
    code, page = http("GET", f"/run/{run_id}")
    assert code == 200 and "Settled" in page, page[:500]
    # profit printed as "profit X.YY"
    import re

    m = re.search(r"profit ([0-9.-]+)", page)
    assert m, page[:500]
    # convert credits string to cents
    return int(round(float(m.group(1)) * 100))


def main() -> int:
    db = ROOT / "smoke_seedstreet.db"
    if db.exists():
        db.unlink()
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "seedstreet.py"), "--seed", "7", "--port", str(PORT), "--db", str(db)],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_up()
        code, home = http("GET", "/")
        assert code == 200 and "SeedStreet" in home
        p1 = flow_profit("SmokeA")
        p2 = flow_profit("SmokeB")
        assert p1 == p2, f"determinism failed: {p1} != {p2}"
        code, lb = http("GET", "/leaderboard?seed=7")
        assert code == 200 and "SmokeA" in lb and "SmokeB" in lb
        print(f"SMOKE OK profit_cents={p1}")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
