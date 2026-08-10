#!/usr/bin/env python3
"""LevelLens — Engineering Resume Signal & Leveling Analyzer."""

from __future__ import annotations

import csv
import io
import json
import math
import re
import sqlite3
import time
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "levellens.db"
FIXTURES = ROOT / "fixtures"
STATIC = ROOT / "static"

# ---------- Lexicon (curated ~120 skills across 6 clusters) ----------

CLUSTERS: dict[str, list[str]] = {
    "Languages": [
        "python", "javascript", "typescript", "java", "go", "golang", "rust", "c++", "c#",
        "ruby", "kotlin", "swift", "scala", "sql", "bash", "shell",
    ],
    "Frontend": [
        "react", "vue", "angular", "html", "css", "sass", "webpack", "vite", "next.js",
        "redux", "tailwind", "svelte", "jquery",
    ],
    "Backend": [
        "fastapi", "django", "flask", "express", "node.js", "spring", "graphql", "rest",
        "grpc", "kafka", "rabbitmq", "redis", "postgres", "postgresql", "mysql", "mongodb",
        "elasticsearch", "nginx",
    ],
    "Data/ML": [
        "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch", "spark",
        "airflow", "dbt", "feature store", "mlflow", "xgboost", "llm", "nlp", "computer vision",
    ],
    "Infra/DevOps": [
        "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform", "ansible",
        "ci/cd", "jenkins", "github actions", "prometheus", "grafana", "linux", "helm",
    ],
    "Leadership/Process": [
        "mentored", "mentoring", "owned", "architected", "drove", "led", "roadmap",
        "stakeholder", "hiring", "onboarding", "agile", "scrum", "design review",
        "incident response", "rfc",
    ],
}

ALIASES = {
    "k8s": "kubernetes",
    "golang": "go",
    "postgres": "postgresql",
    "sklearn": "scikit-learn",
    "node": "node.js",
    "nextjs": "next.js",
    "tf": "tensorflow",
    "js": "javascript",
    "ts": "typescript",
}

SCOPE_VERBS = ["owned", "architected", "drove", "led", "mentored", "designed", "delivered", "scaled"]
LEADERSHIP = ["hiring", "roadmap", "stakeholder", "mentoring", "incident", "rfc", "design review"]

IMPACT_RE = re.compile(
    r"(\d+\s*%|\$\s?\d[\d,]*(?:\.\d+)?[kmb]?|\b\d+\s*(?:users|customers|engineers|people|ms|req/s|qps|TB|GB)\b)",
    re.I,
)
YEAR_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")


def canonical_skill(token: str) -> str:
    t = token.lower().strip()
    return ALIASES.get(t, t)


def all_skills() -> list[str]:
    out: list[str] = []
    for skills in CLUSTERS.values():
        out.extend(skills)
    return sorted(set(canonical_skill(s) for s in out))


def extract_skills(text: str) -> dict[str, list[str]]:
    lower = text.lower()
    found: dict[str, list[str]] = {c: [] for c in CLUSTERS}
    for cluster, skills in CLUSTERS.items():
        for skill in skills:
            canon = canonical_skill(skill)
            # word-ish match
            pat = re.compile(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])", re.I)
            if pat.search(lower) and canon not in found[cluster]:
                found[cluster].append(canon)
    return found


def flatten_skills(by_cluster: dict[str, list[str]]) -> set[str]:
    s: set[str] = set()
    for vals in by_cluster.values():
        s.update(vals)
    return s


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+.#/-]{1,}", text.lower())


def tfidf_cosine(a: str, b: str) -> float:
    """Pure-Python TF-IDF cosine (no sklearn)."""
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    ca, cb = Counter(ta), Counter(tb)
    vocab = sorted(set(ca) | set(cb))
    docs = 2
    idf = {}
    for t in vocab:
        df = (1 if ca[t] else 0) + (1 if cb[t] else 0)
        idf[t] = math.log((1 + docs) / (1 + df)) + 1.0

    def vec(c: Counter) -> list[float]:
        n = sum(c.values()) or 1
        return [(c[t] / n) * idf[t] for t in vocab]

    va, vb = vec(ca), vec(cb)
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va)) or 1.0
    nb = math.sqrt(sum(x * x for x in vb)) or 1.0
    return max(0.0, min(1.0, dot / (na * nb)))


def estimate_years(text: str) -> float:
    years = sorted(int(y) for y in YEAR_RE.findall(text))
    if len(years) >= 2:
        return float(max(0, max(years) - min(years)))
    # fallback: "N years"
    m = re.search(r"(\d+)\+?\s*years?", text, re.I)
    return float(m.group(1)) if m else 0.0


def seniority_score(text: str, impact_count: int, skills: set[str]) -> tuple[float, str]:
    lower = text.lower()
    scope = sum(1 for v in SCOPE_VERBS if v in lower)
    lead = sum(1 for v in LEADERSHIP if v in lower)
    years = estimate_years(text)
    # Documented weights
    score = (
        min(impact_count, 8) * 8.0
        + min(scope, 6) * 6.0
        + min(lead, 5) * 5.0
        + min(years, 15) * 2.5
        + min(len(skills), 20) * 1.0
    )
    score = max(0.0, min(100.0, score))
    if score < 25:
        band = "IC3"
    elif score < 40:
        band = "IC4"
    elif score < 55:
        band = "IC5"
    elif score < 70:
        band = "IC6"
    else:
        band = "IC7"
    return score, band


def analyze(resume_text: str, jd_text: str) -> dict[str, Any]:
    r_skills = extract_skills(resume_text)
    j_skills = extract_skills(jd_text)
    r_set, j_set = flatten_skills(r_skills), flatten_skills(j_skills)
    coverage = (len(r_set & j_set) / len(j_set)) if j_set else 0.0
    sim = tfidf_cosine(resume_text, jd_text)
    match = round(100.0 * (0.55 * sim + 0.45 * coverage), 1)

    impacts = IMPACT_RE.findall(resume_text)
    r_score, r_band = seniority_score(resume_text, len(impacts), r_set)
    j_score, j_band = seniority_score(jd_text, len(IMPACT_RE.findall(jd_text)), j_set)

    # gaps ranked by JD frequency
    jd_tokens = Counter(tokenize(jd_text))
    gaps = sorted(
        [s for s in j_set if s not in r_set],
        key=lambda s: -jd_tokens.get(s, 0),
    )

    radar = {}
    for cluster in CLUSTERS:
        r_n = len(r_skills[cluster])
        j_n = len(j_skills[cluster])
        radar[cluster] = {
            "resume": r_n,
            "jd": j_n,
            "resume_norm": min(1.0, r_n / 4.0),
            "jd_norm": min(1.0, j_n / 4.0),
        }

    recs = []
    for g in gaps[:5]:
        freq = sum(1 for t in tokenize(jd_text) if canonical_skill(t) == g or t == g)
        recs.append(f"JD references '{g}' {max(1, freq)}×; absent from resume")
    if len(impacts) < 4 and r_band in {"IC6", "IC7", "IC5"}:
        recs.append(f"{len(impacts)} quantified impact signal(s) found; IC6+ resumes typically show 4+")
    if not r_set:
        recs.append("Zero lexicon skill hits — check that the resume is text-extractable")

    return {
        "match_score": match,
        "skill_coverage": round(100.0 * coverage, 1),
        "tfidf_similarity": round(100.0 * sim, 1),
        "seniority_score": round(r_score, 1),
        "seniority_band": r_band,
        "jd_seniority_score": round(j_score, 1),
        "jd_seniority_band": j_band,
        "resume_skills": r_skills,
        "jd_skills": j_skills,
        "skill_gaps": gaps,
        "impact_signals": impacts[:20],
        "impact_count": len(impacts),
        "years_estimate": estimate_years(resume_text),
        "radar": radar,
        "recommendations": recs,
        "formula": {
            "match": "0.55*tfidf_cosine + 0.45*skill_coverage",
            "seniority": "8*min(impacts,8)+6*min(scope,6)+5*min(lead,5)+2.5*min(years,15)+1*min(skills,20)",
        },
    }


# ---------- Ingest ----------

def extract_text(file_bytes: bytes, filename: str) -> str:
    import os
    from io import BytesIO

    ext = os.path.splitext(filename)[1].lower()
    if ext == ".txt" or ext == "":
        return file_bytes.decode("utf-8", errors="replace")
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(file_bytes))
        parts = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)
        if not parts:
            raise ValueError("PDF contains no extractable text (possible scanned image)")
        return "\n".join(parts)
    if ext == ".docx":
        from docx import Document

        doc = Document(BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Unsupported file type: {ext}")


# ---------- DB ----------

def conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    c = conn()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS resume_assets (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          filename TEXT NOT NULL,
          mime TEXT NOT NULL,
          raw_text TEXT NOT NULL,
          char_count INTEGER NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS job_descriptions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          raw_text TEXT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS analysis_runs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          resume_id INTEGER NOT NULL,
          jd_id INTEGER NOT NULL,
          mode TEXT NOT NULL,
          match_score REAL NOT NULL,
          seniority_band TEXT NOT NULL,
          seniority_score REAL NOT NULL,
          skill_coverage REAL NOT NULL,
          scores_json TEXT NOT NULL,
          duration_ms INTEGER NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    c.commit()
    c.close()


def persist_run(resume_name: str, resume_text: str, jd_title: str, jd_text: str, mode: str, result: dict, ms: int) -> int:
    c = conn()
    cur = c.execute(
        "INSERT INTO resume_assets (filename, mime, raw_text, char_count) VALUES (?,?,?,?)",
        (resume_name, "text/plain", resume_text, len(resume_text)),
    )
    rid = cur.lastrowid
    cur = c.execute(
        "INSERT INTO job_descriptions (title, raw_text) VALUES (?,?)",
        (jd_title, jd_text),
    )
    jid = cur.lastrowid
    cur = c.execute(
        """INSERT INTO analysis_runs
           (resume_id, jd_id, mode, match_score, seniority_band, seniority_score, skill_coverage, scores_json, duration_ms)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            rid,
            jid,
            mode,
            result["match_score"],
            result["seniority_band"],
            result["seniority_score"],
            result["skill_coverage"],
            json.dumps(result),
            ms,
        ),
    )
    aid = cur.lastrowid
    c.commit()
    c.close()
    return int(aid)


# ---------- App ----------

app = FastAPI(title="LevelLens", version="1.0.0")
init_db()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    ms = int((time.perf_counter() - t0) * 1000)
    print(f"{request.method} {request.url.path} {resp.status_code} {ms}ms", flush=True)
    return resp


@app.get("/api/health")
def health():
    return {"status": "ok", "product": "LevelLens"}


@app.post("/api/analyze/text")
async def analyze_text(
    resume_text: str = Form(...),
    jd_text: str = Form(...),
    jd_title: str = Form("Target role"),
):
    if len(jd_text.strip()) < 50:
        raise HTTPException(400, detail={"code": "jd_too_short", "message": "JD must be at least 50 characters"})
    if not resume_text.strip():
        raise HTTPException(400, detail={"code": "empty_resume", "message": "Resume text is empty"})
    t0 = time.perf_counter()
    result = analyze(resume_text, jd_text)
    ms = int((time.perf_counter() - t0) * 1000)
    aid = persist_run("pasted.txt", resume_text, jd_title, jd_text, "live", result, ms)
    return {"analysis_id": aid, "mode": "live", "duration_ms": ms, **result}


@app.post("/api/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    jd_text: str = Form(...),
    jd_title: str = Form("Target role"),
):
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, detail={"code": "file_too_large", "message": "Max 5 MB"})
    try:
        text = extract_text(data, file.filename or "upload.txt")
    except ValueError as e:
        raise HTTPException(400, detail={"code": "extract_failed", "message": str(e)})
    if len(jd_text.strip()) < 50:
        raise HTTPException(400, detail={"code": "jd_too_short", "message": "JD must be at least 50 characters"})
    t0 = time.perf_counter()
    result = analyze(text, jd_text)
    ms = int((time.perf_counter() - t0) * 1000)
    aid = persist_run(file.filename or "upload", text, jd_title, jd_text, "live", result, ms)
    return {"analysis_id": aid, "mode": "live", "duration_ms": ms, **result}


@app.get("/api/analyses")
def list_analyses(limit: int = 20):
    c = conn()
    rows = c.execute(
        """SELECT a.id, a.mode, a.match_score, a.seniority_band, a.skill_coverage, a.duration_ms, a.created_at,
                  r.filename, j.title as jd_title
           FROM analysis_runs a
           JOIN resume_assets r ON r.id=a.resume_id
           JOIN job_descriptions j ON j.id=a.jd_id
           ORDER BY a.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    c.close()
    return {"analyses": [dict(r) for r in rows]}


@app.get("/api/analyses/{aid}")
def get_analysis(aid: int):
    c = conn()
    row = c.execute("SELECT * FROM analysis_runs WHERE id=?", (aid,)).fetchone()
    c.close()
    if not row:
        raise HTTPException(404, detail={"code": "not_found", "message": "Unknown analysis"})
    d = dict(row)
    d["scores"] = json.loads(d.pop("scores_json"))
    return d


@app.get("/api/analyses/{aid}/export")
def export_analysis(aid: int, format: str = "json"):
    c = conn()
    row = c.execute("SELECT * FROM analysis_runs WHERE id=?", (aid,)).fetchone()
    c.close()
    if not row:
        raise HTTPException(404, detail={"code": "not_found", "message": "Unknown analysis"})
    scores = json.loads(row["scores_json"])
    if format == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["field", "value"])
        for k in ("match_score", "seniority_band", "seniority_score", "skill_coverage"):
            w.writerow([k, scores.get(k, row[k] if k in row.keys() else "")])
        for g in scores.get("skill_gaps", []):
            w.writerow(["skill_gap", g])
        return Response(buf.getvalue(), media_type="text/csv")
    return JSONResponse(scores)


@app.post("/api/demo/seed")
def demo_seed():
    """Seed 3 resumes × 2 JDs through the real pipeline."""
    ensure_fixtures()
    created = []
    resumes = {
        "strong-senior.txt": (FIXTURES / "strong-senior.txt").read_text(encoding="utf-8"),
        "junior-mismatch.txt": (FIXTURES / "junior-mismatch.txt").read_text(encoding="utf-8"),
        "career-changer.txt": (FIXTURES / "career-changer.txt").read_text(encoding="utf-8"),
    }
    jds = {
        "Staff Backend Engineer": (FIXTURES / "jd-staff-backend.txt").read_text(encoding="utf-8"),
        "Frontend Platform Lead": (FIXTURES / "jd-frontend-lead.txt").read_text(encoding="utf-8"),
    }
    for rname, rtext in resumes.items():
        for jtitle, jtext in jds.items():
            t0 = time.perf_counter()
            result = analyze(rtext, jtext)
            ms = int((time.perf_counter() - t0) * 1000)
            aid = persist_run(rname, rtext, jtitle, jtext, "demo", result, ms)
            created.append({"analysis_id": aid, "resume": rname, "jd": jtitle, "match_score": result["match_score"]})
    return {"mode": "demo", "seeded": created, "banner": "DEMO — seeded fixtures via real pipeline"}


def ensure_fixtures() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    files = {
        "strong-senior.txt": """Alex Rivera — Staff Software Engineer
2015-2024 | Owned payments platform serving 2.4M users. Architected event-driven services in Python and Go.
Drove Kubernetes migration on AWS; cut p99 latency 35%. Mentored 6 engineers; led design reviews and RFCs.
Stack: Python, FastAPI, PostgreSQL, Redis, Kafka, Docker, Kubernetes, Terraform, CI/CD, GraphQL.
Led hiring loop; roadmap ownership for fraud detection (scikit-learn + feature store). Incident response on-call.
""",
        "junior-mismatch.txt": """Sam Lee — Junior Developer
2022-2024 Bootcamp graduate. Built React pages and basic Node.js APIs for class projects.
Familiar with HTML, CSS, JavaScript, Git. Internship: fixed bugs in a Django admin panel.
Looking for IC3 frontend roles. No production ownership yet.
""",
        "career-changer.txt": """Jordan Park — Former Data Analyst transitioning to Backend
2018-2023 SQL, pandas, Airflow pipelines; dbt models for revenue dashboards (12 stakeholders).
2023-2024: shipped FastAPI microservices, Docker, PostgreSQL. Drove one internal tool used by 80 people.
Learning Kubernetes and Terraform. Mentored two analysts on Python.
""",
        "jd-staff-backend.txt": """Staff Backend Engineer (IC6)
Own high-scale APIs in Python/Go. Architected event systems with Kafka, Redis, PostgreSQL.
Must have Kubernetes, AWS, Terraform, CI/CD, observability (Prometheus/Grafana).
Leadership: mentored engineers, design reviews, RFCs, hiring. Impact: latency, reliability, millions of users.
Nice: GraphQL, FastAPI, fraud/ML feature store experience.
""",
        "jd-frontend-lead.txt": """Frontend Platform Lead
Lead React/TypeScript platform. Own design system, Vite/webpack tooling, accessibility.
Drive roadmap with stakeholders; mentor IC3–IC5 engineers. Experience with GraphQL and CI/CD required.
Kubernetes knowledge helpful for preview environments. Quantified UX/perf impact expected.
""",
    }
    for name, text in files.items():
        path = FIXTURES / name
        if not path.exists():
            path.write_text(text.strip() + "\n", encoding="utf-8")


ensure_fixtures()

# Static UI last so /api wins
if STATIC.exists():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")


def main():
    import uvicorn

    print("LevelLens -> http://127.0.0.1:8000/", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
