"""HivePulse core library"""
import csv
import json
import math
import os
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any

MetricSeries = namedtuple('MetricSeries', ['timestamps', 'values', 'metadata'])
AnomalyWindow = namedtuple('AnomalyWindow', ['start', 'end', 'detector', 'peak_score', 'direction', 'sample_count', 'reason'])
AnalysisRun = namedtuple('AnalysisRun', ['run_id', 'input_file', 'detector', 'threshold', 'preset', 'timestamp', 'windows'])

DATA_DIR = Path(__file__).parent.parent / 'hivepulse_data'
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / 'history.json'

def _load_history() -> List[Dict[str, Any]]:
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def _save_history(entry: Dict[str, Any]):
    hist = _load_history()
    hist.append(entry)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(hist, f, indent=2)

def parse_csv(path: str) -> MetricSeries:
    timestamps = []
    values = []
    rejected = 0
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # auto-detect columns
        cols = reader.fieldnames
        if not cols:
            raise ValueError('CSV has no header')
        # try common names
        ts_col = next((c for c in cols if 'time' in c.lower() or 'date' in c.lower()), None)
        val_col = next((c for c in cols if 'weight' in c.lower() or 'value' in c.lower() or 'metric' in c.lower()), None)
        if not ts_col or not val_col:
            raise ValueError('Could not auto-detect timestamp or metric column')
        seen_ts = set()
        for row in reader:
            try:
                ts_raw = row[ts_col].strip()
                val_raw = row[val_col].strip()
                if not ts_raw or not val_raw:
                    raise ValueError('empty cell')
                # parse timestamp – accept ISO or common formats
                try:
                    ts = datetime.fromisoformat(ts_raw)
                except Exception:
                    ts = datetime.strptime(ts_raw, '%Y-%m-%d %H:%M:%S')
                val = float(val_raw)
                if ts in seen_ts:
                    continue  # dedupe, keep first
                seen_ts.add(ts)
                timestamps.append(ts)
                values.append(val)
            except Exception:
                rejected += 1
    if not timestamps:
        raise ValueError('No valid rows after parsing')
    # sort by timestamp
    combined = sorted(zip(timestamps, values), key=lambda x: x[0])
    timestamps, values = zip(*combined)
    metadata = {'row_count': len(timestamps), 'rejected_rows': rejected}
    return MetricSeries(list(timestamps), list(values), metadata)

def _zscore_flags(values: List[float], threshold: float) -> List[bool]:
    if len(values) < 2:
        return [False] * len(values)
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    std = math.sqrt(var)
    if std == 0:
        return [False] * len(values)
    return [abs((v - mean) / std) >= threshold for v in values]

def _iqr_flags(values: List[float], k: float) -> List[bool]:
    if len(values) < 4:
        return [False] * len(values)
    sorted_vals = sorted(values)
    q1 = sorted_vals[int(len(sorted_vals) * 0.25)]
    q3 = sorted_vals[int(len(sorted_vals) * 0.75)]
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    return [v < lower or v > upper for v in values]

def _merge_flags(timestamps: List[datetime], values: List[float], flags: List[bool], detector: str) -> List[AnomalyWindow]:
    windows = []
    i = 0
    n = len(flags)
    while i < n:
        if flags[i]:
            start_idx = i
            # extend while consecutive flagged
            while i + 1 < n and flags[i + 1]:
                i += 1
            end_idx = i
            segment_vals = values[start_idx:end_idx + 1]
            peak = max(segment_vals, key=lambda v: abs(v - sum(values) / len(values)))
            # compute score: for zscore we could reuse flag value, but we keep simple
            score = abs(peak - sum(values) / len(values))
            direction = 'spike' if peak > sum(values) / len(values) else 'drop'
            reason = f"{detector.upper()} anomaly ({direction})"
            windows.append(AnomalyWindow(
                start=timestamps[start_idx].isoformat(),
                end=timestamps[end_idx].isoformat(),
                detector=detector,
                peak_score=score,
                direction=direction,
                sample_count=end_idx - start_idx + 1,
                reason=reason,
            ))
        i += 1
    return windows

def detect(series: MetricSeries, detector: str, threshold: float) -> List[AnomalyWindow]:
    if detector == 'zscore':
        flags = _zscore_flags(series.values, threshold)
    elif detector == 'iqr':
        flags = _iqr_flags(series.values, threshold)  # here threshold is k
    else:
        raise ValueError('Unsupported detector')
    return _merge_flags(series.timestamps, series.values, flags, detector)

def plot(series: MetricSeries, windows: List[AnomalyWindow]):
    # Very simple ASCII plot: print timestamp and value, mark anomaly with '*'
    anomaly_indices = set()
    for w in windows:
        start = datetime.fromisoformat(w.start)
        end = datetime.fromisoformat(w.end)
        for idx, ts in enumerate(series.timestamps):
            if start <= ts <= end:
                anomaly_indices.add(idx)
    for idx, (ts, val) in enumerate(zip(series.timestamps, series.values)):
        marker = '*' if idx in anomaly_indices else ' '
        print(f"{ts.isoformat()} {marker} {val:.2f}")

def export_report(run_id: str, input_file: str, detector: str, threshold: float, preset: str, windows: List[AnomalyWindow], export_path: str):
    report = {
        'run_id': run_id,
        'input_file': input_file,
        'detector': detector,
        'threshold': threshold,
        'preset': preset,
        'timestamp': datetime.utcnow().isoformat(),
        'windows': [w._asdict() for w in windows],
    }
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    # also record in history
    _save_history({
        'run_id': run_id,
        'input_file': input_file,
        'detector': detector,
        'threshold': threshold,
        'preset': preset,
        'timestamp': report['timestamp'],
        'window_count': len(windows),
        'export_path': str(Path(export_path).resolve())
    })
    return report
