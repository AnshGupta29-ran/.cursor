"""Unit tests for EpochLedger pure logic: verdicts, rank correlation, instability, validation."""
import math
import pytest

from app import (
    compute_verdict,
    detect_instability,
    rank_correlation,
    pearson,
    _rank,
    slugify,
    LogBatch,
    MetricPoint,
)


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------

def _exp(champion_id=None, policy=None):
    return {
        "id": "exp1",
        "champion_run_id": champion_id,
        "gate_policy": policy or {"primary_metric": "f1", "min_delta_pct": 1.0},
    }


def _run(metrics=None, status="FINISHED"):
    return {
        "id": "r1",
        "status": status,
        "metrics": metrics or {},
        "params": {},
    }


def test_verdict_no_champion_inconclusive():
    import app
    app.runs.clear()
    v = compute_verdict(_run({"f1": [{"step": 0, "value": 0.9}]}), _exp())
    assert v["verdict"] == "INCONCLUSIVE"
    assert "champion" in v["summary"].lower()


def test_verdict_failed_run_inconclusive():
    v = compute_verdict(_run(status="FAILED"), _exp(champion_id="c"))
    assert v["verdict"] == "INCONCLUSIVE"
    assert "failed" in v["summary"].lower()


def test_verdict_running_inconclusive():
    v = compute_verdict(_run(status="RUNNING"), _exp(champion_id="c"))
    assert v["verdict"] == "INCONCLUSIVE"


def test_verdict_pass():
    import app
    app.runs.clear()
    champ = _run({"f1": [{"step": 0, "value": 0.80}]})
    app.runs["c"] = champ
    run = _run({"f1": [{"step": 0, "value": 0.84}]})  # +5%
    v = compute_verdict(run, _exp(champion_id="c"))
    assert v["verdict"] == "PASS"
    assert "+" in v["summary"]


def test_verdict_regressed():
    import app
    app.runs.clear()
    app.runs["c"] = _run({"f1": [{"step": 0, "value": 0.80}]})
    run = _run({"f1": [{"step": 0, "value": 0.70}]})  # -12.5%
    v = compute_verdict(run, _exp(champion_id="c"))
    assert v["verdict"] == "REGRESSED"


def test_verdict_below_min_delta_regressed():
    import app
    app.runs.clear()
    app.runs["c"] = _run({"f1": [{"step": 0, "value": 0.80}]})
    run = _run({"f1": [{"step": 0, "value": 0.801}]})  # +0.125% < 1% gate
    v = compute_verdict(run, _exp(champion_id="c", policy={"primary_metric": "f1", "min_delta_pct": 1.0}))
    assert v["verdict"] == "REGRESSED"


def test_verdict_missing_metric_inconclusive():
    import app
    app.runs.clear()
    app.runs["c"] = _run({"f1": [{"step": 0, "value": 0.80}]})
    run = _run({"accuracy": [{"step": 0, "value": 0.9}]})  # no f1
    v = compute_verdict(run, _exp(champion_id="c"))
    assert v["verdict"] == "INCONCLUSIVE"
    assert "no 'f1'" in v["summary"]


def test_verdict_guard_metric_regressed():
    import app
    app.runs.clear()
    app.runs["c"] = _run({
        "f1": [{"step": 0, "value": 0.80}],
        "latency_ms": [{"step": 0, "value": 50.0}],
    })
    run = _run({
        "f1": [{"step": 0, "value": 0.85}],   # primary improved
        "latency_ms": [{"step": 0, "value": 90.0}],  # guard regressed +80%
    })
    policy = {"primary_metric": "f1", "min_delta_pct": 1.0,
              "guard_metric": "latency_ms", "guard_max_regress_pct": 10.0}
    v = compute_verdict(run, _exp(champion_id="c", policy=policy))
    assert v["verdict"] == "REGRESSED"
    assert "guard" in v["summary"].lower()


# ---------------------------------------------------------------------------
# Rank correlation
# ---------------------------------------------------------------------------

def test_rank_handles_ties():
    assert _rank([1, 2, 2, 4]) == [1.0, 2.5, 2.5, 4.0]


def test_pearson_perfect():
    assert abs(pearson([1, 2, 3], [2, 4, 6]) - 1.0) < 1e-9


def test_pearson_zero_variance():
    assert pearson([1, 1, 1], [1, 2, 3]) == 0.0


def test_rank_correlation_monotonic_positive():
    assert rank_correlation([1, 2, 3, 4, 5], [10, 20, 30, 40, 50]) > 0.99


def test_rank_correlation_monotonic_negative():
    assert rank_correlation([1, 2, 3, 4, 5], [50, 40, 30, 20, 10]) < -0.99


def test_rank_correlation_no_relation():
    r = rank_correlation([1, 2, 3, 4], [2, 1, 4, 3])
    assert -1.0 <= r <= 1.0  # just must be a valid coefficient


# ---------------------------------------------------------------------------
# Instability detection
# ---------------------------------------------------------------------------

def test_instability_detects_spike():
    series = [{"step": i, "value": 0.8} for i in range(5)]
    series.append({"step": 5, "value": 0.4})  # big spike down
    series += [{"step": i, "value": 0.8} for i in range(6, 10)]
    notes = detect_instability(series)
    assert any("step 5" in n for n in notes)


def test_instability_smooth_series_none():
    series = [{"step": i, "value": 0.8 + i * 0.001} for i in range(12)]
    assert detect_instability(series) == []


def test_instability_short_series_none():
    series = [{"step": i, "value": float(i)} for i in range(4)]
    assert detect_instability(series) == []


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_metric_point_rejects_nan():
    with pytest.raises(Exception):
        MetricPoint(step=0, value=float("nan"))


def test_metric_point_rejects_inf():
    with pytest.raises(Exception):
        MetricPoint(step=0, value=float("inf"))


def test_logbatch_rejects_bad_param_type():
    with pytest.raises(Exception):
        LogBatch(params={"nested": {"a": 1}})


def test_logbatch_accepts_valid():
    b = LogBatch(params={"lr": 0.01, "opt": "adam", "flag": True},
                 metrics={"f1": [{"step": 0, "value": 0.8}]})
    assert b.params["lr"] == 0.01


def test_slugify():
    assert slugify("my report!.txt") == "my-report-.txt"
    assert slugify("../../etc/passwd") == "etc-passwd"
    assert slugify("") == "artifact"
    assert "/" not in slugify("a/b/c.txt")
