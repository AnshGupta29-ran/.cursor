"""EpochLedger — Offline-First ML Experiment Journal with Champion/Challenger Gates.

Fully offline, in-memory persistence only. No accounts, no cloud calls, no model downloads.
"""
import csv
import io
import json
import math
import random
import re
import threading
import time
import uuid
from collections import deque
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# In-memory stores (memory_only persistence)
# ---------------------------------------------------------------------------

_lock = threading.Lock()

experiments: Dict[str, Dict] = {}
runs: Dict[str, Dict] = {}
artifacts: Dict[str, Dict] = {}
api_activity: deque = deque(maxlen=100)  # ring buffer

ARTIFACT_MAX_BYTES = 1 * 1024 * 1024          # 1 MB per artifact
RUN_ARTIFACT_MAX_BYTES = 25 * 1024 * 1024     # 25 MB per run

app = FastAPI(title="EpochLedger", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Middleware: API activity log
# ---------------------------------------------------------------------------

@app.middleware("http")
async def activity_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    if request.url.path.startswith("/api"):
        api_activity.append(
            {
                "timestamp": time.time(),
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": latency_ms,
            }
        )
    return response


# ---------------------------------------------------------------------------
# Error envelope helper
# ---------------------------------------------------------------------------

def err(status: int, code: str, message: str):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "error", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


# ---------------------------------------------------------------------------
# Pydantic models with validation
# ---------------------------------------------------------------------------

class GatePolicy(BaseModel):
    primary_metric: str = "f1"
    min_delta_pct: float = 0.0
    guard_metric: Optional[str] = None
    guard_max_regress_pct: Optional[float] = None


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    gate_policy: Optional[GatePolicy] = None


class RunStart(BaseModel):
    experiment_id: str
    name: str = Field(min_length=1, max_length=120)
    tags: Optional[List[str]] = []


class MetricPoint(BaseModel):
    step: float
    value: float

    @field_validator("value")
    @classmethod
    def finite_value(cls, v):
        if not math.isfinite(v):
            raise ValueError("metric value must be finite (no NaN/inf)")
        return v

    @field_validator("step")
    @classmethod
    def finite_step(cls, v):
        if not math.isfinite(v):
            raise ValueError("step must be finite")
        return v


class LogBatch(BaseModel):
    params: Optional[Dict[str, Any]] = {}
    metrics: Optional[Dict[str, List[MetricPoint]]] = {}

    @field_validator("params")
    @classmethod
    def valid_params(cls, v):
        if v is None:
            return {}
        for k, val in v.items():
            if not isinstance(k, str):
                raise ValueError("param keys must be strings")
            if not isinstance(val, (str, int, float, bool)):
                raise ValueError(f"param '{k}' must be str/number/bool")
            if isinstance(val, float) and not math.isfinite(val):
                raise ValueError(f"param '{k}' must be finite")
        return v


class ChampionSet(BaseModel):
    run_id: str
    policy: Optional[GatePolicy] = None


class TagSet(BaseModel):
    tags: List[str]


# ---------------------------------------------------------------------------
# Gate / verdict logic (pure functions — unit-testable)
# ---------------------------------------------------------------------------

def last_metric_value(run: Dict, metric: str) -> Optional[float]:
    series = run.get("metrics", {}).get(metric)
    if not series:
        return None
    return series[-1]["value"]


def compute_verdict(run: Dict, experiment: Dict) -> Dict:
    """Return {verdict: PASS|REGRESSED|INCONCLUSIVE, summary: str}"""
    if run.get("status") == "FAILED":
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "Run failed — cannot evaluate against champion.",
        }
    if run.get("status") == "RUNNING":
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "Run is still in progress — finish it before gate evaluation.",
        }

    champion_id = experiment.get("champion_run_id")
    if not champion_id:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "No champion pinned yet — set a champion to enable promotion gates.",
        }
    champion = runs.get(champion_id)
    if not champion:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": "Champion run was deleted — re-pin a champion to enable gates.",
        }

    policy = experiment.get("gate_policy") or {}
    primary = policy.get("primary_metric", "f1")
    min_delta_pct = policy.get("min_delta_pct", 0.0)

    champ_val = last_metric_value(champion, primary)
    run_val = last_metric_value(run, primary)

    if champ_val is None:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"Champion has no '{primary}' metric recorded.",
        }
    if run_val is None:
        return {
            "verdict": "INCONCLUSIVE",
            "summary": f"This run has no '{primary}' metric — cannot compare to champion.",
        }

    # Guard metric check (latency/cost-style: an *increase* beyond the allowed
    # pct counts as a regression and blocks promotion even if the primary improved)
    guard = policy.get("guard_metric")
    guard_max_regress = policy.get("guard_max_regress_pct")
    if guard and guard_max_regress is not None:
        champ_guard = last_metric_value(champion, guard)
        run_guard = last_metric_value(run, guard)
        if champ_guard is not None and run_guard is not None and champ_guard != 0:
            guard_delta_pct = ((run_guard - champ_guard) / abs(champ_guard)) * 100
            if guard_delta_pct > abs(guard_max_regress):
                return {
                    "verdict": "REGRESSED",
                    "summary": (
                        f"REGRESSED: guard metric '{guard}' rose {guard_delta_pct:.1f}% "
                        f"({champ_guard:.4f} → {run_guard:.4f}), exceeding the allowed {guard_max_regress}% regression."
                    ),
                }

    if champ_val == 0:
        delta_pct = 0.0 if run_val == 0 else float("inf")
    else:
        delta_pct = ((run_val - champ_val) / abs(champ_val)) * 100

    if delta_pct >= min_delta_pct:
        return {
            "verdict": "PASS",
            "summary": (
                f"PASS: {primary} improved {delta_pct:+.2f}% vs champion "
                f"({champ_val:.4f} → {run_val:.4f}), meeting the {min_delta_pct}% gate."
            ),
        }
    return {
        "verdict": "REGRESSED",
        "summary": (
            f"REGRESSED: {primary} moved {delta_pct:+.2f}% vs champion "
            f"({champ_val:.4f} → {run_val:.4f}), below the required +{min_delta_pct}% gate."
        ),
    }


# ---------------------------------------------------------------------------
# Instability detection (deterministic, stdlib only)
# ---------------------------------------------------------------------------

def detect_instability(series: List[Dict]) -> List[str]:
    """Flag points deviating >3× rolling MAD from rolling median."""
    notes = []
    if len(series) < 5:
        return notes
    values = [p["value"] for p in series]
    window = 5
    for i in range(window, len(values)):
        w = values[i - window : i]
        med = sorted(w)[len(w) // 2]
        abs_devs = sorted(abs(v - med) for v in w)
        mad = abs_devs[len(abs_devs) // 2]
        if mad == 0:
            mad = 1e-9
        if abs(values[i] - med) > 3 * mad:
            notes.append(f"instability near step {series[i]['step']}")
    return notes


# ---------------------------------------------------------------------------
# Rank correlation (Pearson over ranks, stdlib only — no scipy)
# ---------------------------------------------------------------------------

def _rank(values: List[float]) -> List[float]:
    """Return average ranks (1-based) handling ties."""
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j + 2) / 2.0  # 1-based average
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def pearson(x: List[float], y: List[float]) -> float:
    n = len(x)
    if n < 2:
        return 0.0
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den_x = math.sqrt(sum((a - mx) ** 2 for a in x))
    den_y = math.sqrt(sum((b - my) ** 2 for b in y))
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


def rank_correlation(param_vals: List[float], metric_vals: List[float]) -> float:
    return pearson(_rank(param_vals), _rank(metric_vals))


def param_influence(experiment_id: str) -> Dict:
    """Top-3 numeric param drivers correlated with primary metric."""
    exp = experiments.get(experiment_id)
    if not exp:
        return {"drivers": [], "message": "Experiment not found."}
    policy = exp.get("gate_policy") or {}
    primary = policy.get("primary_metric", "f1")
    finished = [
        runs[rid]
        for rid in exp.get("runs", [])
        if runs.get(rid, {}).get("status") == "FINISHED"
    ]
    if len(finished) < 4:
        return {
            "drivers": [],
            "message": f"Need at least 4 finished runs to compute influence (have {len(finished)}).",
        }
    # collect numeric params
    param_keys = set()
    for r in finished:
        for k, v in r.get("params", {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                param_keys.add(k)
    metric_vals = []
    valid_runs = []
    for r in finished:
        mv = last_metric_value(r, primary)
        if mv is not None:
            metric_vals.append(mv)
            valid_runs.append(r)
    if len(valid_runs) < 4:
        return {
            "drivers": [],
            "message": f"Fewer than 4 runs have the primary metric '{primary}'.",
        }
    scored = []
    for k in sorted(param_keys):
        pvals = []
        mvals = []
        for r, mv in zip(valid_runs, metric_vals):
            pv = r.get("params", {}).get(k)
            if isinstance(pv, (int, float)) and not isinstance(pv, bool):
                pvals.append(float(pv))
                mvals.append(mv)
        if len(pvals) >= 4 and len(set(pvals)) > 1:
            corr = rank_correlation(pvals, mvals)
            scored.append({"param": k, "correlation": round(corr, 3), "abs": abs(corr)})
    scored.sort(key=lambda s: -s["abs"])
    drivers = []
    for s in scored[:3]:
        direction = "higher" if s["correlation"] > 0 else "lower"
        strength = (
            "strongly" if s["abs"] >= 0.7 else "moderately" if s["abs"] >= 0.4 else "weakly"
        )
        drivers.append(
            {
                "param": s["param"],
                "correlation": s["correlation"],
                "explanation": (
                    f"'{s['param']}' is {strength} correlated with {primary}: "
                    f"{direction} values tend to {'improve' if s['correlation'] > 0 else 'hurt'} {primary}."
                ),
            }
        )
    return {"drivers": drivers, "message": "" if drivers else "No numeric params vary across runs."}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    return s[:80] or "artifact"


def run_artifact_bytes(run_id: str) -> int:
    return sum(a["size"] for a in artifacts.values() if a["run_id"] == run_id)


def find_experiment_for_run(run_id: str) -> Optional[Dict]:
    run = runs.get(run_id)
    if not run:
        return None
    return experiments.get(run["experiment_id"])


# ---------------------------------------------------------------------------
# API: health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "experiments": len(experiments), "runs": len(runs)}


# ---------------------------------------------------------------------------
# API: experiments
# ---------------------------------------------------------------------------

@app.post("/api/experiments", status_code=201)
def create_experiment(payload: ExperimentCreate):
    with _lock:
        exp_id = uuid.uuid4().hex[:12]
        experiments[exp_id] = {
            "id": exp_id,
            "name": payload.name,
            "created_at": time.time(),
            "champion_run_id": None,
            "gate_policy": (payload.gate_policy or GatePolicy()).model_dump(),
            "runs": [],
        }
    return experiments[exp_id]


@app.get("/api/experiments")
def list_experiments():
    out = []
    for e in experiments.values():
        out.append({**e, "run_count": len(e["runs"])})
    return out


@app.get("/api/experiments/{exp_id}")
def get_experiment(exp_id: str):
    e = experiments.get(exp_id)
    if not e:
        raise HTTPException(404, {"code": "not_found", "message": f"Experiment '{exp_id}' not found"})
    exp_runs = [runs[rid] for rid in e["runs"] if rid in runs]
    return {**e, "run_objects": exp_runs}


@app.put("/api/experiments/{exp_id}/champion")
def set_champion(exp_id: str, payload: ChampionSet):
    e = experiments.get(exp_id)
    if not e:
        raise HTTPException(404, {"code": "not_found", "message": f"Experiment '{exp_id}' not found"})
    if payload.run_id not in runs:
        raise HTTPException(404, {"code": "not_found", "message": f"Run '{payload.run_id}' not found"})
    if runs[payload.run_id]["experiment_id"] != exp_id:
        raise HTTPException(422, {"code": "mismatch", "message": "Run does not belong to this experiment"})
    e["champion_run_id"] = payload.run_id
    if payload.policy:
        e["gate_policy"] = payload.policy.model_dump()
    return {"ok": True, "champion_run_id": payload.run_id, "gate_policy": e["gate_policy"]}


@app.delete("/api/experiments/{exp_id}/runs/{run_id}")
def delete_run(exp_id: str, run_id: str):
    e = experiments.get(exp_id)
    if not e:
        raise HTTPException(404, {"code": "not_found", "message": "Experiment not found"})
    if run_id not in e["runs"]:
        raise HTTPException(404, {"code": "not_found", "message": "Run not in experiment"})
    e["runs"].remove(run_id)
    if e.get("champion_run_id") == run_id:
        e["champion_run_id"] = None  # deleting champion clears the gate
    runs.pop(run_id, None)
    for aid in [a for a in artifacts if artifacts[a]["run_id"] == run_id]:
        artifacts.pop(aid, None)
    return {"ok": True, "champion_cleared": e.get("champion_run_id") is None}


# ---------------------------------------------------------------------------
# API: runs
# ---------------------------------------------------------------------------

@app.post("/api/runs", status_code=201)
def start_run(payload: RunStart):
    e = experiments.get(payload.experiment_id)
    if not e:
        raise HTTPException(404, {"code": "not_found", "message": f"Experiment '{payload.experiment_id}' not found"})
    with _lock:
        run_id = uuid.uuid4().hex[:12]
        run = {
            "id": run_id,
            "experiment_id": payload.experiment_id,
            "name": payload.name,
            "status": "RUNNING",
            "tags": payload.tags or [],
            "params": {},
            "metrics": {},
            "started_at": time.time(),
            "finished_at": None,
        }
        runs[run_id] = run
        e["runs"].append(run_id)
    return run


@app.post("/api/runs/{run_id}/log-batch")
def log_batch(run_id: str, payload: LogBatch):
    run = runs.get(run_id)
    if not run:
        raise HTTPException(404, {"code": "not_found", "message": f"Run '{run_id}' not found"})
    if run["status"] != "RUNNING":
        raise HTTPException(409, {"code": "conflict", "message": f"Run is {run['status']} — cannot log"})
    with _lock:
        for k, v in (payload.params or {}).items():
            run["params"][k] = v
        for mk, points in (payload.metrics or {}).items():
            series = run["metrics"].setdefault(mk, [])
            for p in points:
                series.append({"step": p.step, "value": p.value})
    return {"ok": True, "params": run["params"], "metric_keys": list(run["metrics"].keys())}


@app.post("/api/runs/{run_id}/finish")
def finish_run(run_id: str):
    run = runs.get(run_id)
    if not run:
        raise HTTPException(404, {"code": "not_found", "message": "Run not found"})
    if run["status"] != "RUNNING":
        raise HTTPException(409, {"code": "conflict", "message": f"Run already {run['status']}"})
    run["status"] = "FINISHED"
    run["finished_at"] = time.time()
    return run


@app.post("/api/runs/{run_id}/fail")
def fail_run(run_id: str):
    run = runs.get(run_id)
    if not run:
        raise HTTPException(404, {"code": "not_found", "message": "Run not found"})
    run["status"] = "FAILED"
    run["finished_at"] = time.time()
    return run


@app.post("/api/runs/{run_id}/tags")
def tag_run(run_id: str, payload: TagSet):
    run = runs.get(run_id)
    if not run:
        raise HTTPException(404, {"code": "not_found", "message": "Run not found"})
    run["tags"] = payload.tags
    return {"ok": True, "tags": run["tags"]}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    run = runs.get(run_id)
    if not run:
        raise HTTPException(404, {"code": "not_found", "message": "Run not found"})
    # attach instability notes per metric
    notes = {}
    for mk, series in run.get("metrics", {}).items():
        n = detect_instability(series)
        if n:
            notes[mk] = n
    return {**run, "curve_notes": notes}


@app.get("/api/runs/{run_id}/verdict")
def get_verdict(run_id: str):
    run = runs.get(run_id)
    if not run:
        raise HTTPException(404, {"code": "not_found", "message": "Run not found"})
    exp = find_experiment_for_run(run_id)
    if not exp:
        raise HTTPException(404, {"code": "not_found", "message": "Parent experiment not found"})
    return compute_verdict(run, exp)


@app.get("/api/experiments/{exp_id}/influence")
def get_influence(exp_id: str):
    if exp_id not in experiments:
        raise HTTPException(404, {"code": "not_found", "message": "Experiment not found"})
    return param_influence(exp_id)


@app.get("/api/experiments/{exp_id}/compare")
def compare_runs(exp_id: str, run_ids: str = ""):
    e = experiments.get(exp_id)
    if not e:
        raise HTTPException(404, {"code": "not_found", "message": "Experiment not found"})
    ids = [r for r in run_ids.split(",") if r][:4]
    selected = [runs[rid] for rid in ids if rid in runs and runs[rid]["experiment_id"] == exp_id]
    if not selected:
        raise HTTPException(422, {"code": "no_runs", "message": "Provide up to 4 valid run_ids from this experiment"})
    champion = runs.get(e.get("champion_run_id") or "")
    policy = e.get("gate_policy") or {}
    primary = policy.get("primary_metric", "f1")

    # param diff: keys where values differ
    all_keys = set()
    for r in selected:
        all_keys.update(r.get("params", {}).keys())
    param_diff = {}
    for k in sorted(all_keys):
        vals = [r.get("params", {}).get(k) for r in selected]
        param_diff[k] = {"values": vals, "differs": len(set(map(repr, vals))) > 1}

    identical = all(not v["differs"] for v in param_diff.values()) and len(selected) > 1

    champ_primary = last_metric_value(champion, primary) if champion else None
    rows = []
    for r in selected:
        rv = last_metric_value(r, primary)
        delta_pct = None
        if champ_primary is not None and rv is not None and champ_primary != 0:
            delta_pct = round(((rv - champ_primary) / abs(champ_primary)) * 100, 2)
        rows.append(
            {
                "id": r["id"],
                "name": r["name"],
                "status": r["status"],
                "params": r.get("params", {}),
                "primary_value": rv,
                "delta_vs_champion_pct": delta_pct,
                "verdict": compute_verdict(r, e),
            }
        )
    return {
        "experiment": e["name"],
        "primary_metric": primary,
        "champion_run_id": e.get("champion_run_id"),
        "runs": rows,
        "param_diff": param_diff,
        "identical_configs": identical,
    }


# ---------------------------------------------------------------------------
# API: artifacts
# ---------------------------------------------------------------------------

@app.post("/api/runs/{run_id}/artifacts", status_code=201)
async def upload_artifact(run_id: str, request: Request):
    run = runs.get(run_id)
    if not run:
        raise HTTPException(404, {"code": "not_found", "message": "Run not found"})
    body = await request.body()
    if len(body) > ARTIFACT_MAX_BYTES:
        return err(413, "too_large", f"Artifact exceeds 1MB cap ({len(body)} bytes)")
    if run_artifact_bytes(run_id) + len(body) > RUN_ARTIFACT_MAX_BYTES:
        return err(413, "too_large", "Run artifact storage exceeds 25MB cap")
    name = request.query_params.get("name", "artifact")
    content_type = request.query_params.get("content_type", "text/plain")
    slug = slugify(name)
    aid = uuid.uuid4().hex[:12]
    artifacts[aid] = {
        "id": aid,
        "run_id": run_id,
        "name": slug,
        "content_type": content_type,
        "size": len(body),
        "bytes": body,
        "created_at": time.time(),
    }
    return {"id": aid, "name": slug, "size": len(body), "content_type": content_type}


@app.get("/api/runs/{run_id}/artifacts")
def list_artifacts(run_id: str):
    if run_id not in runs:
        raise HTTPException(404, {"code": "not_found", "message": "Run not found"})
    return [
        {k: v for k, v in a.items() if k != "bytes"}
        for a in artifacts.values()
        if a["run_id"] == run_id
    ]


@app.get("/api/artifacts/{aid}")
def download_artifact(aid: str):
    a = artifacts.get(aid)
    if not a:
        raise HTTPException(404, {"code": "not_found", "message": "Artifact not found"})
    return Response(content=a["bytes"], media_type=a["content_type"],
                    headers={"Content-Disposition": f'attachment; filename="{a["name"]}"'})


@app.get("/api/artifacts/{aid}/preview")
def preview_artifact(aid: str):
    a = artifacts.get(aid)
    if not a:
        raise HTTPException(404, {"code": "not_found", "message": "Artifact not found"})
    ct = a["content_type"]
    if ct.startswith("text/") or ct in ("application/json", "text/csv"):
        text = a["bytes"][:4000].decode("utf-8", errors="replace")
        return {"name": a["name"], "content_type": ct, "preview": text}
    return err(415, "unsupported", "Preview only supported for text/JSON/CSV artifacts")


# ---------------------------------------------------------------------------
# API: activity
# ---------------------------------------------------------------------------

@app.get("/api/activity")
def get_activity():
    return list(api_activity)


# ---------------------------------------------------------------------------
# API: demo seed (deterministic)
# ---------------------------------------------------------------------------

SEED_EXP_NAME = "sentiment-sweep"


def _generate_curve(base: float, noise_amp: float, spike_at: Optional[int], rng: random.Random, steps: int = 12):
    series = []
    for s in range(steps):
        val = base + 0.012 * math.log1p(s) + rng.uniform(-noise_amp, noise_amp)
        if spike_at is not None and s == spike_at:
            val -= 0.18  # deliberate instability spike
        series.append({"step": s, "value": round(val, 4)})
    return series


@app.post("/api/demo/seed")
def seed_demo():
    # Idempotent: return existing if already seeded
    for e in experiments.values():
        if e["name"] == SEED_EXP_NAME:
            return {"seeded": False, "experiment_id": e["id"], "message": "Already seeded"}

    rng = random.Random(42)  # fixed seed → deterministic
    exp_id = uuid.uuid4().hex[:12]
    policy = GatePolicy(primary_metric="f1", min_delta_pct=1.0,
                        guard_metric="latency_ms", guard_max_regress_pct=10.0)
    experiments[exp_id] = {
        "id": exp_id,
        "name": SEED_EXP_NAME,
        "created_at": time.time(),
        "champion_run_id": None,
        "gate_policy": policy.model_dump(),
        "runs": [],
    }

    configs = [
        {"learning_rate": 0.001, "batch_size": 32, "dropout": 0.1, "optimizer": "adam"},
        {"learning_rate": 0.003, "batch_size": 32, "dropout": 0.1, "optimizer": "adam"},
        {"learning_rate": 0.005, "batch_size": 64, "dropout": 0.2, "optimizer": "adam"},
        {"learning_rate": 0.010, "batch_size": 64, "dropout": 0.2, "optimizer": "sgd"},
        {"learning_rate": 0.020, "batch_size": 128, "dropout": 0.3, "optimizer": "sgd"},
        {"learning_rate": 0.030, "batch_size": 128, "dropout": 0.3, "optimizer": "adam"},
        {"learning_rate": 0.050, "batch_size": 256, "dropout": 0.4, "optimizer": "sgd"},
        {"learning_rate": 0.100, "batch_size": 256, "dropout": 0.5, "optimizer": "sgd"},
    ]
    # f1 peaks around lr=0.01, latency rises with batch_size
    f1_bases = [0.71, 0.76, 0.80, 0.84, 0.82, 0.79, 0.74, 0.66]

    run_ids = []
    for i, (cfg, f1b) in enumerate(zip(configs, f1_bases)):
        rid = uuid.uuid4().hex[:12]
        # introduce a deliberate instability spike in runs idx 1 and 4
        spike = 6 if i in (1, 4) else None
        f1_series = _generate_curve(f1b, 0.0015, spike, rng)
        lat_base = 40 + cfg["batch_size"] * 0.35
        lat_series = [{"step": s, "value": round(lat_base + rng.uniform(-2, 2), 2)} for s in range(12)]
        runs[rid] = {
            "id": rid,
            "experiment_id": exp_id,
            "name": f"sweep-lr{cfg['learning_rate']}-bs{cfg['batch_size']}",
            "status": "FINISHED",
            "tags": ["seed", "sweep"],
            "params": dict(cfg),
            "metrics": {"f1": f1_series, "latency_ms": lat_series},
            "started_at": time.time() - 3600 + i * 60,
            "finished_at": time.time() - 3600 + i * 60 + 300,
        }
        experiments[exp_id]["runs"].append(rid)
        run_ids.append(rid)

    # Champion: run with lr=0.01 (index 3, f1_base 0.84)
    experiments[exp_id]["champion_run_id"] = run_ids[3]

    # Seed one text artifact on champion
    report = (
        "classification report — champion run\n"
        "====================================\n"
        "              precision    recall  f1-score   support\n"
        "    negative       0.85      0.83      0.84       500\n"
        "     neutral       0.80      0.82      0.81       300\n"
        "    positive       0.86      0.85      0.85       200\n"
        "    accuracy                           0.84      1000\n"
    )
    aid = uuid.uuid4().hex[:12]
    artifacts[aid] = {
        "id": aid,
        "run_id": run_ids[3],
        "name": "classification-report.txt",
        "content_type": "text/plain",
        "size": len(report.encode()),
        "bytes": report.encode(),
        "created_at": time.time(),
    }

    return {"seeded": True, "experiment_id": exp_id, "champion_run_id": run_ids[3], "runs": run_ids}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
