#!/usr/bin/env python3
"""
SeedStreet Exchange — Meridian Archipelago paper-trading arena.

Deterministic, seed-locked trading floor (stdlib only: http.server + sqlite3).
CLI: python seedstreet.py --seed 7 --port 8080 --db seedstreet.db [--snapshot]
"""

from __future__ import annotations

import argparse
import html
import math
import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
STARTING_CASH = 1_000_000  # cents = 10_000 credits
MAX_TICK = 239
FEE_BPS = 15  # 0.15%
MIN_FEE = 100  # 1 credit in cents
SYMBOLS = ["KELP", "BRINE", "AMBR", "SALTGLASS", "CORAL"]
SECTORS = ["Seafood", "Water", "Amber", "Glass", "Coral"]

# ---------- SplitMix64 (version-stable PRNG) ----------


class SplitMix64:
    def __init__(self, seed: int):
        self.state = (seed + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF

    def uint64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return z ^ (z >> 31)

    def float64(self) -> float:
        return (self.uint64() >> 11) * (1.0 / (1 << 53))

    def intn(self, n: int) -> int:
        if n <= 0:
            return 0
        return self.uint64() % n


def hash_symbol(sym: str) -> int:
    h = 2166136261
    for ch in sym.encode():
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def instruments_for_seed(seed: int) -> list[dict[str, Any]]:
    rng = SplitMix64(seed)
    out = []
    for i, sym in enumerate(SYMBOLS):
        out.append(
            {
                "symbol": sym,
                "name": f"{sym} Flats",
                "sector": SECTORS[i],
                "base": 1000 + rng.intn(9000),
                "drift": rng.float64() * 0.001 - 0.0005,
                "vol": rng.float64() * 0.02 + 0.01,
            }
        )
    return out


def event_ticks(seed: int) -> list[int]:
    rng = SplitMix64(seed + 12345)
    ticks = sorted({rng.intn(200) + 20 for _ in range(3)})
    while len(ticks) < 3:
        ticks.append(rng.intn(200) + 20)
        ticks = sorted(set(ticks))
    return ticks[:3]


def price_cents(seed: int, symbol: str, tick: int) -> int:
    instr = next(i for i in instruments_for_seed(seed) if i["symbol"] == symbol)
    events = event_ticks(seed)
    event_set = set(events)
    rng = SplitMix64(seed + hash_symbol(symbol))
    log_p = math.log(float(instr["base"]))
    for t in range(tick + 1):
        u1 = max(1e-12, rng.float64())
        u2 = rng.float64()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2 * math.pi * u2)
        log_p += instr["drift"] + instr["vol"] * z
        if t in event_set:
            for idx, et in enumerate(events):
                if et == t and instr["sector"] == SECTORS[idx % len(SECTORS)]:
                    log_p += (rng.float64() - 0.5) * 0.12
                    break
    return max(1, int(round(math.exp(log_p))))


def fee_cents(notional: int) -> int:
    return max(MIN_FEE, notional * FEE_BPS // 10000)


def fmt_credits(cents: int) -> str:
    return f"{cents / 100:.2f}"


def svg_chart(seed: int, symbol: str, upto: int, width: int = 280, height: int = 80) -> str:
    pts = [price_cents(seed, symbol, t) for t in range(upto + 1)]
    if not pts:
        return ""
    mn, mx = min(pts), max(pts)
    span = max(1, mx - mn)
    coords = []
    for i, p in enumerate(pts):
        x = 0 if len(pts) == 1 else i * (width - 1) / (len(pts) - 1)
        y = height - 1 - (p - mn) * (height - 1) / span
        coords.append(f"{x:.1f},{y:.1f}")
    poly = " ".join(coords)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(symbol)} chart">'
        f'<polyline fill="none" stroke="#0b3d2e" stroke-width="1.5" points="{poly}"/>'
        f"</svg>"
    )


# ---------- DB ----------


class Store:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              seed INTEGER NOT NULL,
              handle TEXT NOT NULL,
              cash INTEGER NOT NULL,
              tick INTEGER NOT NULL,
              status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS trades (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER NOT NULL,
              tick INTEGER NOT NULL,
              symbol TEXT NOT NULL,
              side TEXT NOT NULL,
              qty INTEGER NOT NULL,
              price INTEGER NOT NULL,
              fee INTEGER NOT NULL,
              FOREIGN KEY(run_id) REFERENCES runs(id)
            );
            """
        )
        self.conn.commit()

    def execute(self, sql: str, args: tuple = ()):
        with self._lock:
            cur = self.conn.execute(sql, args)
            self.conn.commit()
            return cur

    def query(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self.conn.execute(sql, args))

    def query_one(self, sql: str, args: tuple = ()) -> sqlite3.Row | None:
        rows = self.query(sql, args)
        return rows[0] if rows else None


# ---------- Game logic ----------


class Engine:
    def __init__(self, store: Store, default_seed: int, snapshot: bool):
        self.store = store
        self.default_seed = default_seed
        self.snapshot = snapshot
        if snapshot:
            self._ensure_snapshot()

    def _ensure_snapshot(self) -> None:
        row = self.store.query_one(
            "SELECT id FROM runs WHERE seed=? AND handle=? AND status='active'",
            (7, "SnapshotTrader"),
        )
        if row:
            return
        run_id = self.new_run("SnapshotTrader", 7)
        self.trade(run_id, "KELP", "buy", 40)
        self.advance(run_id, 10)
        self.trade(run_id, "KELP", "sell", 20)
        self.advance(run_id, 30)

    def new_run(self, handle: str, seed: int) -> int:
        cur = self.store.execute(
            "INSERT INTO runs (seed, handle, cash, tick, status) VALUES (?,?,?,?,?)",
            (seed, handle or "Trader", STARTING_CASH, 0, "active"),
        )
        return int(cur.lastrowid)

    def get_run(self, run_id: int) -> sqlite3.Row | None:
        return self.store.query_one("SELECT * FROM runs WHERE id=?", (run_id,))

    def holdings(self, run_id: int) -> dict[str, int]:
        h: dict[str, int] = {s: 0 for s in SYMBOLS}
        for t in self.store.query(
            "SELECT symbol, side, qty FROM trades WHERE run_id=? ORDER BY id", (run_id,)
        ):
            h[t["symbol"]] += t["qty"] if t["side"] == "buy" else -t["qty"]
        return h

    def equity(self, run: sqlite3.Row) -> int:
        tick = run["tick"]
        total = run["cash"]
        for sym, qty in self.holdings(run["id"]).items():
            if qty:
                total += qty * price_cents(run["seed"], sym, tick)
        return total

    def trade(self, run_id: int, symbol: str, side: str, qty: int) -> str | None:
        run = self.get_run(run_id)
        if not run:
            return "Unknown run"
        if run["status"] != "active":
            return "Run already settled"
        symbol = symbol.upper()
        if symbol not in SYMBOLS:
            return "Unknown instrument"
        if qty <= 0:
            return "Qty must be positive whole shares"
        side = side.lower()
        if side not in ("buy", "sell"):
            return "Side must be buy or sell"
        px = price_cents(run["seed"], symbol, run["tick"])
        notional = px * qty
        fee = fee_cents(notional)
        cash = run["cash"]
        held = self.holdings(run_id)[symbol]
        if side == "buy":
            cost = notional + fee
            if cost > cash:
                return "Insufficient credits — order rejected"
            cash -= cost
        else:
            if qty > held:
                return "Oversell — order rejected"
            cash += notional - fee
        self.store.execute(
            "UPDATE runs SET cash=? WHERE id=?", (cash, run_id)
        )
        self.store.execute(
            "INSERT INTO trades (run_id, tick, symbol, side, qty, price, fee) VALUES (?,?,?,?,?,?,?)",
            (run_id, run["tick"], symbol, side, qty, px, fee),
        )
        return None

    def advance(self, run_id: int, steps: int) -> str | None:
        run = self.get_run(run_id)
        if not run:
            return "Unknown run"
        if run["status"] != "active":
            return "Run already settled"
        new_tick = min(MAX_TICK, run["tick"] + max(0, steps))
        self.store.execute("UPDATE runs SET tick=? WHERE id=?", (new_tick, run_id))
        if new_tick >= MAX_TICK:
            self.settle(run_id)
        return None

    def settle(self, run_id: int) -> str | None:
        run = self.get_run(run_id)
        if not run:
            return "Unknown run"
        if run["status"] == "settled":
            return None  # idempotent
        # force tick to close
        tick = max(run["tick"], MAX_TICK)
        self.store.execute("UPDATE runs SET tick=? WHERE id=?", (tick, run_id))
        run = self.get_run(run_id)
        assert run
        cash = run["cash"]
        for sym, qty in self.holdings(run_id).items():
            if qty > 0:
                px = price_cents(run["seed"], sym, tick)
                notional = px * qty
                fee = fee_cents(notional)
                cash += notional - fee
                self.store.execute(
                    "INSERT INTO trades (run_id, tick, symbol, side, qty, price, fee) VALUES (?,?,?,?,?,?,?)",
                    (run_id, tick, sym, "sell", qty, px, fee),
                )
        self.store.execute(
            "UPDATE runs SET cash=?, tick=?, status='settled' WHERE id=?",
            (cash, tick, run_id),
        )
        return None

    def leaderboard(self, seed: int | None = None) -> list[dict[str, Any]]:
        if seed is None:
            rows = self.store.query(
                "SELECT * FROM runs WHERE status='settled' ORDER BY (cash - ?) DESC, tick ASC, id ASC",
                (STARTING_CASH,),
            )
        else:
            rows = self.store.query(
                "SELECT * FROM runs WHERE status='settled' AND seed=? ORDER BY (cash - ?) DESC, tick ASC, id ASC",
                (seed, STARTING_CASH),
            )
        out = []
        for r in rows:
            profit = r["cash"] - STARTING_CASH
            out.append(
                {
                    "id": r["id"],
                    "handle": r["handle"],
                    "seed": r["seed"],
                    "profit": profit,
                    "cash": r["cash"],
                    "tick": r["tick"],
                }
            )
        return out


# ---------- HTML ----------

CSS = """
:root { --ink:#102a22; --paper:#f4f0e6; --accent:#c45c26; --line:#1e4d3a; }
*{box-sizing:border-box} body{margin:0;font:16px/1.45 Georgia,serif;background:linear-gradient(165deg,#e8efe9,#f4f0e6 40%,#efe6d6);color:var(--ink)}
header{padding:1.2rem 1.5rem;border-bottom:2px solid var(--line);background:#0f2f26;color:#f4f0e6}
header a{color:#f4f0e6;margin-right:1rem}
main{max-width:980px;margin:0 auto;padding:1.25rem}
h1,h2{font-family:Palatino,Georgia,serif;letter-spacing:.02em}
.card{background:rgba(255,255,255,.72);border:1px solid #c9d5cc;padding:1rem;margin:1rem 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}
label{display:block;margin:.4rem 0 .2rem}
input,select,button{font:inherit;padding:.35rem .55rem}
button,.btn{background:var(--accent);color:#fff;border:0;cursor:pointer;text-decoration:none;display:inline-block}
.error{color:#8b1e1e;font-weight:bold}
table{width:100%;border-collapse:collapse} th,td{border-bottom:1px solid #c9d5cc;padding:.35rem;text-align:left}
.banner{background:#214c3a;color:#f4f0e6;padding:.75rem 1rem;margin:1rem 0}
.muted{opacity:.75;font-size:.92rem}
"""


def layout(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)} · SeedStreet</title>
<style>{CSS}</style></head>
<body>
<header>
  <strong>SeedStreet Exchange</strong> — <em>Same seed, same storm.</em>
  <div><a href="/">Floor desk</a><a href="/leaderboard">Leaderboard</a></div>
</header>
<main>{body}</main>
</body></html>"""


def render_home(engine: Engine, error: str = "") -> str:
    lb = engine.leaderboard()[:10]
    rows = "".join(
        f"<tr><td>{html.escape(r['handle'])}</td><td>{r['seed']}</td>"
        f"<td>{fmt_credits(r['profit'])}</td>"
        f"<td><a href='/run/{r['id']}/tape'>tape</a></td></tr>"
        for r in lb
    ) or "<tr><td colspan=4 class=muted>No settled runs yet.</td></tr>"
    err = f"<p class=error>{html.escape(error)}</p>" if error else ""
    body = f"""
    <h1>Meridian Archipelago · Trading Desk</h1>
    <p class=muted>One compressed market day = 240 ticks. Long-only, fee 0.15% (min 1 credit).</p>
    {err}
    <div class=card>
      <h2>Open a run</h2>
      <form method=post action="/run/new">
        <label>Handle <input name=handle value=Trader required></label>
        <label>Seed <input name=seed type=number value={engine.default_seed}></label>
        <p><button type=submit>Ring the floor bell</button></p>
      </form>
    </div>
    <div class=card>
      <h2>Leaderboard (recent)</h2>
      <table><tr><th>Handle</th><th>Seed</th><th>Profit</th><th></th></tr>{rows}</table>
    </div>
    """
    return layout("Home", body)


def render_floor(engine: Engine, run: sqlite3.Row, error: str = "") -> str:
    seed = run["seed"]
    tick = run["tick"]
    events = event_ticks(seed)
    banners = []
    for i, et in enumerate(events):
        if tick >= et:
            sector = SECTORS[i % len(SECTORS)]
            banners.append(
                f"<div class=banner>Dispatch @ tick {et}: Storm over the {sector.lower()} flats — {sector} sector shock.</div>"
            )
    holdings = engine.holdings(run["id"])
    eq = engine.equity(run)
    cards = []
    for instr in instruments_for_seed(seed):
        sym = instr["symbol"]
        px = price_cents(seed, sym, tick)
        cards.append(
            f"""<div class=card>
            <h3>{html.escape(sym)} · {html.escape(instr['name'])}</h3>
            <p class=muted>{html.escape(instr['sector'])} · mark {fmt_credits(px)}</p>
            {svg_chart(seed, sym, tick)}
            <p>Held: {holdings[sym]}</p>
            </div>"""
        )
    err = f"<p class=error>{html.escape(error)}</p>" if error else ""
    settled = run["status"] == "settled"
    forms = ""
    if not settled:
        forms = f"""
        <div class=card>
          <h2>Order ticket</h2>
          <form method=post action="/run/{run['id']}/trade">
            <label>Symbol <select name=symbol>{''.join(f'<option>{s}</option>' for s in SYMBOLS)}</select></label>
            <label>Side <select name=side><option>buy</option><option>sell</option></select></label>
            <label>Qty <input name=qty type=number min=1 value=10></label>
            <p><button type=submit>Submit order</button></p>
          </form>
        </div>
        <div class=card>
          <h2>Advance clock</h2>
          <form method=post action="/run/{run['id']}/advance" style="display:flex;gap:.5rem;flex-wrap:wrap">
            <button name=steps value=1>Advance 1</button>
            <button name=steps value=10>Advance 10</button>
            <button name=steps value=30>Advance 30</button>
            <button name=steps value=999>To close</button>
          </form>
          <form method=post action="/run/{run['id']}/settle" style="margin-top:.75rem">
            <button type=submit>Settlement bell</button>
          </form>
        </div>
        """
    else:
        profit = run["cash"] - STARTING_CASH
        forms = f"""
        <div class=card>
          <h2>Settled</h2>
          <p>Final equity {fmt_credits(run['cash'])} · profit {fmt_credits(profit)}
          ({(profit/STARTING_CASH)*100:.2f}%)</p>
          <p><a class=btn href="/run/{run['id']}/tape">Trade tape</a>
             <a class=btn href="/leaderboard?seed={seed}">Seed leaderboard</a></p>
        </div>
        """
    body = f"""
    <h1>Floor · {html.escape(run['handle'])}</h1>
    <p>Run #{run['id']} · seed {seed} · tick {tick}/{MAX_TICK} · status {run['status']}</p>
    <p>Cash {fmt_credits(run['cash'])} · Equity {fmt_credits(eq)}</p>
    {''.join(banners)}
    {err}
    <div class=grid>{''.join(cards)}</div>
    {forms}
    """
    return layout(f"Run {run['id']}", body)


def render_tape(engine: Engine, run: sqlite3.Row) -> str:
    trades = engine.store.query(
        "SELECT * FROM trades WHERE run_id=? ORDER BY id", (run["id"],)
    )
    rows = "".join(
        f"<tr><td>{t['tick']}</td><td>{html.escape(t['symbol'])}</td>"
        f"<td>{t['side']}</td><td>{t['qty']}</td>"
        f"<td>{fmt_credits(t['price'])}</td><td>{fmt_credits(t['fee'])}</td></tr>"
        for t in trades
    ) or "<tr><td colspan=6 class=muted>No trades.</td></tr>"
    body = f"""
    <h1>Trade tape · {html.escape(run['handle'])}</h1>
    <p><a href="/run/{run['id']}">Back to floor</a></p>
    <table><tr><th>Tick</th><th>Sym</th><th>Side</th><th>Qty</th><th>Price</th><th>Fee</th></tr>{rows}</table>
    """
    return layout("Tape", body)


def render_leaderboard(engine: Engine, seed: int | None) -> str:
    rows_data = engine.leaderboard(seed)
    rows = "".join(
        f"<tr><td>{i+1}</td><td>{html.escape(r['handle'])}</td><td>{r['seed']}</td>"
        f"<td>{fmt_credits(r['profit'])}</td>"
        f"<td><a href='/run/{r['id']}/tape'>tape</a></td></tr>"
        for i, r in enumerate(rows_data)
    ) or "<tr><td colspan=5 class=muted>Empty board.</td></tr>"
    body = f"""
    <h1>Leaderboard</h1>
    <form method=get><label>Filter seed <input name=seed value="{'' if seed is None else seed}"></label>
    <button type=submit>Filter</button></form>
    <table><tr><th>#</th><th>Handle</th><th>Seed</th><th>Profit</th><th></th></tr>{rows}</table>
    """
    return layout("Leaderboard", body)


# ---------- HTTP ----------


class Handler(BaseHTTPRequestHandler):
    engine: Engine

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _send(self, code: int, body: str, content_type: str = "text/html; charset=utf-8") -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, loc: str) -> None:
        self.send_response(303)
        self.send_header("Location", loc)
        self.end_headers()

    def _read_form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        qs = parse_qs(raw, keep_blank_values=True)
        return {k: (v[-1] if v else "") for k, v in qs.items()}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/":
            if self.engine.snapshot:
                row = self.engine.store.query_one(
                    "SELECT * FROM runs WHERE handle=? ORDER BY id DESC LIMIT 1",
                    ("SnapshotTrader",),
                )
                if row:
                    self._send(200, render_floor(self.engine, row))
                    return
            self._send(200, render_home(self.engine))
            return

        if path == "/leaderboard":
            seed = None
            if "seed" in qs and qs["seed"][0].strip():
                try:
                    seed = int(qs["seed"][0])
                except ValueError:
                    seed = None
            self._send(200, render_leaderboard(self.engine, seed))
            return

        if path.startswith("/run/"):
            parts = [p for p in path.split("/") if p]
            # ['run', id, ...]
            try:
                run_id = int(parts[1])
            except (IndexError, ValueError):
                self._send(404, layout("404", "<p>Not found</p>"))
                return
            run = self.engine.get_run(run_id)
            if not run:
                self._send(404, layout("404", "<p>Unknown run</p>"))
                return
            if len(parts) >= 3 and parts[2] == "tape":
                self._send(200, render_tape(self.engine, run))
                return
            self._send(200, render_floor(self.engine, run))
            return

        self._send(404, layout("404", "<p>Not found</p>"))

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        form = self._read_form()

        if path == "/run/new":
            try:
                seed = int(form.get("seed") or self.engine.default_seed)
            except ValueError:
                seed = self.engine.default_seed
            rid = self.engine.new_run(form.get("handle", "Trader"), seed)
            self._redirect(f"/run/{rid}")
            return

        if path.startswith("/run/"):
            parts = [p for p in path.split("/") if p]
            try:
                run_id = int(parts[1])
                action = parts[2] if len(parts) > 2 else ""
            except (IndexError, ValueError):
                self._send(404, layout("404", "<p>Not found</p>"))
                return
            run = self.engine.get_run(run_id)
            if not run:
                self._send(404, layout("404", "<p>Unknown run</p>"))
                return
            err = None
            if action == "trade":
                try:
                    qty = int(form.get("qty") or "0")
                except ValueError:
                    qty = 0
                err = self.engine.trade(run_id, form.get("symbol", ""), form.get("side", ""), qty)
            elif action == "advance":
                try:
                    steps = int(form.get("steps") or "1")
                except ValueError:
                    steps = 1
                if steps >= 900:
                    steps = MAX_TICK - run["tick"]
                err = self.engine.advance(run_id, steps)
            elif action == "settle":
                err = self.engine.settle(run_id)
            run = self.engine.get_run(run_id)
            assert run
            if err:
                self._send(200, render_floor(self.engine, run, error=err))
            else:
                self._redirect(f"/run/{run_id}")
            return

        self._send(404, layout("404", "<p>Not found</p>"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SeedStreet Exchange")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--db", type=str, default=str(ROOT / "seedstreet.db"))
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--host", type=str, default="127.0.0.1")
    args = ap.parse_args(argv)

    store = Store(Path(args.db))
    engine = Engine(store, args.seed, args.snapshot)
    Handler.engine = engine
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(
        f"SeedStreet Exchange on http://{args.host}:{args.port}/ "
        f"(seed={args.seed}, db={args.db}, snapshot={args.snapshot})",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
