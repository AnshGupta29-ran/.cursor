"""ClerkLens — cited Q&A over municipal meeting packets (Flask + CSV + pure TF-IDF)."""
from __future__ import annotations

import csv
import hashlib
import re
import uuid
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template_string, request, url_for

from retrieval import PROFILES, confidence_band, extractive_answer, rank

APP_ROOT = Path(__file__).parent
DATA_DIR = APP_ROOT / "data"
FIX_DIR = APP_ROOT / "fixtures"
DATA_DIR.mkdir(exist_ok=True)

DOCS = DATA_DIR / "documents.csv"
CHUNKS = DATA_DIR / "chunks.csv"
QUERIES = DATA_DIR / "queries.csv"
ANSWERS = DATA_DIR / "answers.csv"
REQLOG = DATA_DIR / "request_log.csv"
MAX_BYTES = 2 * 1024 * 1024

HEADERS = {
    DOCS: ["doc_id", "filename", "doc_type", "meeting_date", "n_chars", "sha256", "ingested_at"],
    CHUNKS: ["chunk_id", "doc_id", "seq", "start", "end", "text", "token_count"],
    QUERIES: ["query_id", "asked_at", "question", "seed", "profile", "top_k"],
    ANSWERS: [
        "answer_id",
        "query_id",
        "status",
        "confidence_band",
        "answer_text",
        "cited_chunk_ids",
        "latency_ms",
    ],
    REQLOG: ["timestamp", "method", "path", "status_code", "duration_ms"],
}


def init_csvs() -> None:
    for path, header in HEADERS.items():
        if not path.exists():
            with path.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(header)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_text(path: Path) -> tuple[str, str | None]:
    """Return (text, error_message)."""
    ext = path.suffix.lower()
    if ext == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            return "", "Empty text file rejected."
        return text, None
    if ext == ".pdf":
        # Lightweight text-layer stub: only accept tiny demo PDFs we don't ship;
        # scanned/empty PDFs get a distinct message. Prefer .txt fixtures.
        raw = path.read_bytes()
        if len(raw) < 20:
            return "", "Corrupt PDF rejected."
        # Heuristic: if almost no ASCII letters, treat as scanned / no text layer
        ascii_letters = sum(1 for b in raw if 65 <= b <= 90 or 97 <= b <= 122)
        if ascii_letters < 40:
            return "", "Scanned PDF with no extractable text layer — convert to .txt first."
        try:
            text = re.sub(rb"[^\x20-\x7e\n\r\t]+", b" ", raw).decode("ascii", "ignore")
        except Exception:
            text = ""
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 40:
            return "", "Scanned PDF with no extractable text layer — convert to .txt first."
        return text, None
    return "", f"Unsupported file type ({ext}). Only .txt and .pdf."


def chunk_text(text: str, doc_id: str, size: int = 450, overlap: int = 80) -> list[dict]:
    chunks = []
    i = 0
    seq = 0
    n = len(text)
    while i < n:
        end = min(i + size, n)
        # Prefer paragraph boundary near end
        window = text[i:end]
        if end < n:
            cut = window.rfind("\n\n")
            if cut > size // 3:
                end = i + cut
                window = text[i:end]
        cid = f"{doc_id}-c{seq:04d}"
        chunks.append(
            {
                "chunk_id": cid,
                "doc_id": doc_id,
                "seq": seq,
                "start": i,
                "end": end,
                "text": window.strip(),
                "token_count": len(window.split()),
            }
        )
        if end >= n:
            break
        i = max(end - overlap, i + 1)
        seq += 1
    return [c for c in chunks if c["text"]]


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_row(path: Path, row: list) -> None:
    with path.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def infer_doc_type(name: str) -> str:
    n = name.lower()
    if "agenda" in n:
        return "agenda"
    if "minute" in n:
        return "minutes"
    if "ordinance" in n:
        return "ordinance"
    return "minutes"


def ingest_bytes(filename: str, data: bytes) -> tuple[dict | None, str]:
    """Ingest file bytes → (doc_meta, message). Raises via return error string."""
    ext = Path(filename).suffix.lower()
    if ext not in {".txt", ".pdf"}:
        return None, f"Unsupported type for “{filename}” (only .txt / .pdf)."
    if len(data) > MAX_BYTES:
        return None, f"File too large ({len(data)} bytes). Max 2 MB."
    if len(data) == 0:
        return None, f"Empty file rejected: “{filename}”."

    digest = sha256_bytes(data)
    for row in read_rows(DOCS):
        if row.get("sha256") == digest:
            return None, f"Duplicate packet skipped (already ingested as {row.get('doc_id')})."

    tmp = DATA_DIR / f"_tmp_{uuid.uuid4().hex}{ext}"
    tmp.write_bytes(data)
    try:
        text, err = extract_text(tmp)
        if err:
            return None, err
        doc_id = digest[:12]
        meta = {
            "doc_id": doc_id,
            "filename": Path(filename).name,
            "doc_type": infer_doc_type(filename),
            "meeting_date": "2024-03-12" if "2024-03-12" in filename else "",
            "n_chars": len(text),
            "sha256": digest,
            "ingested_at": now_iso(),
        }
        append_row(
            DOCS,
            [
                meta["doc_id"],
                meta["filename"],
                meta["doc_type"],
                meta["meeting_date"],
                meta["n_chars"],
                meta["sha256"],
                meta["ingested_at"],
            ],
        )
        for c in chunk_text(text, doc_id):
            append_row(
                CHUNKS,
                [c["chunk_id"], c["doc_id"], c["seq"], c["start"], c["end"], c["text"], c["token_count"]],
            )
        n_chunks = sum(1 for r in read_rows(CHUNKS) if r["doc_id"] == doc_id)
        return meta, f"Ingested {meta['filename']} as {doc_id} ({meta['doc_type']}) · {n_chunks} chunks."
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def load_sample_corpus() -> list[str]:
    msgs = []
    for path in sorted(FIX_DIR.glob("*.txt")):
        _, msg = ingest_bytes(path.name, path.read_bytes())
        msgs.append(msg)
    return msgs


init_csvs()
app = Flask(__name__)

CSS = """
:root {
  --bg: #eef1f4;
  --ink: #142033;
  --muted: #4d5b6e;
  --panel: #fbfcfd;
  --line: #c5ced9;
  --accent: #0c5c4c;
  --accent2: #1f4b99;
  --warn: #8a4b00;
  --bad: #8b1e1e;
  --chip: #dceee8;
  --banner: #fff4d6;
  font-family: "Source Serif 4", "Iowan Old Style", "Palatino Linotype", Georgia, serif;
}
* { box-sizing: border-box; }
body { margin: 0; background: linear-gradient(180deg, #dfe7ef 0%, var(--bg) 40%, #e8ebe6 100%); color: var(--ink); min-height: 100vh; }
a { color: var(--accent2); }
.wrap { max-width: 1080px; margin: 0 auto; padding: 1.25rem; }
header.site {
  background: #10253f;
  color: #f4f7fb;
  padding: 1.1rem 1.25rem 1.25rem;
  border-bottom: 4px solid var(--accent);
}
header.site h1 { margin: 0; font-size: 1.7rem; letter-spacing: 0.02em; font-weight: 700; }
header.site p { margin: 0.35rem 0 0; color: #c9d4e3; max-width: 46rem; font-size: 0.98rem; }
nav.bar { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.9rem; }
nav.bar a {
  color: #10253f; background: #e8eef7; text-decoration: none;
  padding: 0.35rem 0.75rem; border: 1px solid #9eb0c7; font-size: 0.92rem;
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
}
nav.bar a.active { background: #fff; border-color: #fff; font-weight: 600; }
.panel {
  background: var(--panel); border: 1px solid var(--line); padding: 1rem 1.1rem; margin: 1rem 0;
  box-shadow: 0 1px 0 rgba(20,32,51,0.04);
}
.grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 1rem; }
@media (max-width: 860px) { .grid { grid-template-columns: 1fr; } }
h2 { margin: 0 0 0.6rem; font-size: 1.25rem; }
.muted { color: var(--muted); font-size: 0.95rem; }
.banner {
  background: var(--banner); border: 1px solid #e2c56b; padding: 0.55rem 0.75rem;
  margin: 0.75rem 0; font-family: "IBM Plex Sans", "Segoe UI", sans-serif; font-size: 0.9rem;
}
.ok { color: var(--accent); }
.err { color: var(--bad); }
.warn { color: var(--warn); }
table { width: 100%; border-collapse: collapse; font-size: 0.92rem; font-family: "IBM Plex Sans", "Segoe UI", sans-serif; }
th, td { border-bottom: 1px solid var(--line); text-align: left; padding: 0.45rem 0.3rem; vertical-align: top; }
button, .btn, input[type=submit] {
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
  background: var(--accent); color: #fff; border: 0; padding: 0.45rem 0.85rem; cursor: pointer;
}
button.secondary, a.btn.secondary { background: #fff; color: var(--ink); border: 1px solid var(--line); text-decoration: none; display: inline-block; }
input[type=text], input[type=file], select, textarea {
  font: inherit; width: 100%; padding: 0.45rem; border: 1px solid var(--line); background: #fff;
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
}
label { display: block; margin: 0.6rem 0 0.25rem; font-family: "IBM Plex Sans", "Segoe UI", sans-serif; font-size: 0.9rem; }
.chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.6rem; }
.chip {
  background: var(--chip); border: 1px solid #9fcec0; padding: 0.2rem 0.55rem;
  text-decoration: none; color: var(--accent); font-family: "IBM Plex Sans", "Segoe UI", sans-serif; font-size: 0.85rem;
}
.answer-body { line-height: 1.55; font-size: 1.05rem; }
.evidence { white-space: pre-wrap; font-family: ui-monospace, Consolas, monospace; font-size: 0.88rem; background: #fff; border: 1px solid var(--line); padding: 0.85rem; }
mark { background: #ffe58a; }
.stat { font-family: "IBM Plex Sans", "Segoe UI", sans-serif; font-size: 0.88rem; color: var(--muted); }
"""

BASE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{{ title }} · ClerkLens</title>
  <style>{{ css }}</style>
</head>
<body>
  <header class="site">
    <div class="wrap">
      <h1>ClerkLens</h1>
      <p>Cited extractive Q&amp;A over municipal agendas, minutes, and ordinances — provenance first, abstain over invent.</p>
      <nav class="bar" aria-label="Primary">
        <a href="{{ url_for('index') }}" class="{{ 'active' if nav=='home' else '' }}">Packets</a>
        <a href="{{ url_for('upload') }}" class="{{ 'active' if nav=='upload' else '' }}">Upload</a>
        <a href="{{ url_for('ask') }}" class="{{ 'active' if nav=='ask' else '' }}">Ask</a>
        <a href="{{ url_for('history') }}" class="{{ 'active' if nav=='history' else '' }}">History</a>
      </nav>
    </div>
  </header>
  <main class="wrap">{{ body|safe }}</main>
</body>
</html>
"""


def page(title: str, nav: str, body: str) -> str:
    return render_template_string(BASE, title=title, nav=nav, body=body, css=CSS)


@app.before_request
def _stamp():
    request.start_time = datetime.now(timezone.utc)


@app.after_request
def _log(resp):
    try:
        ms = (datetime.now(timezone.utc) - request.start_time).total_seconds() * 1000
        append_row(REQLOG, [now_iso(), request.method, request.path, resp.status_code, f"{ms:.1f}"])
    except Exception:
        pass
    return resp


@app.get("/health")
@app.get("/healthz")
def health():
    return jsonify(status="ok", docs=len(read_rows(DOCS)), chunks=len(read_rows(CHUNKS)))


@app.get("/")
def index():
    docs = read_rows(DOCS)
    flash = request.args.get("flash")
    rows = "".join(
        f"<tr><td>{escape(d['filename'])}</td><td>{escape(d['doc_type'])}</td>"
        f"<td>{escape(d.get('meeting_date') or '—')}</td><td>{escape(d['n_chars'])}</td>"
        f"<td><code>{escape(d['doc_id'])}</code></td></tr>"
        for d in docs
    ) or "<tr><td colspan=5 class='muted'>No packets yet — load the Riverbend sample corpus or upload.</td></tr>"
    body = f"""
    <div class="grid">
      <section class="panel">
        <h2>Meeting packets in the index</h2>
        <p class="muted">CSV-backed corpus for City of Riverbend civic research. Every answer cites chunk IDs you can open.</p>
        {"<p class='ok'>"+escape(flash)+"</p>" if flash else ""}
        <table>
          <thead><tr><th>File</th><th>Type</th><th>Meeting</th><th>Chars</th><th>doc_id</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        <p class="stat">{len(docs)} document(s) · {len(read_rows(CHUNKS))} chunks · history survives restart</p>
      </section>
      <aside class="panel">
        <h2>Get started</h2>
        <p class="muted">Cold start? Load the sample agenda, minutes (with roll-call), and ordinance excerpt.</p>
        <form method="post" action="{url_for('load_samples')}">
          <button type="submit">Load Riverbend sample corpus</button>
        </form>
        <p style="margin-top:1rem"><a class="btn secondary" href="{url_for('ask')}">Ask a research question</a></p>
        <p class="muted">Try: <em>What was the roll-call vote on the short-term rental ordinance?</em></p>
      </aside>
    </div>
    """
    return page("Packets", "home", body)


@app.post("/load-samples")
def load_samples():
    msgs = load_sample_corpus()
    flash = " · ".join(msgs) if msgs else "No fixture files found."
    return redirect(url_for("index", flash=flash[:400]))


@app.route("/upload", methods=["GET", "POST"])
@app.route("/ingest", methods=["GET", "POST"])
def upload():
    msg = err = None
    if request.method == "POST":
        f = request.files.get("file")
        if not f or not f.filename:
            err = "No file uploaded."
        else:
            data = f.read()
            meta, message = ingest_bytes(f.filename, data)
            if meta is None:
                err = message
            else:
                msg = message
    body = f"""
    <section class="panel">
      <h2>Upload meeting packet</h2>
      <p class="muted">Accepts <strong>.txt</strong> and text-layer <strong>.pdf</strong> ≤ 2&nbsp;MB. Duplicates detected by SHA-256. Scanned PDFs are rejected with a clear message.</p>
      {"<p class='ok'>"+escape(msg)+"</p>" if msg else ""}
      {"<p class='err'>"+escape(err)+"</p>" if err else ""}
      <form method="post" enctype="multipart/form-data">
        <label>Packet file</label>
        <input type="file" name="file" accept=".txt,.pdf,text/plain,application/pdf" required />
        <p style="margin-top:0.8rem"><input type="submit" value="Ingest packet" /></p>
      </form>
    </section>
    """
    return page("Upload", "upload", body)


@app.route("/ask", methods=["GET", "POST"])
def ask():
    result_html = ""
    if request.method == "POST":
        t0 = datetime.now(timezone.utc)
        question = (request.form.get("question") or "").strip()
        profile_name = request.form.get("profile") or "balanced"
        profile = PROFILES.get(profile_name, PROFILES["balanced"])
        if not question or not re.search(r"[A-Za-z0-9]", question):
            abort(400, "Empty or punctuation-only question rejected.")
        chunks = read_rows(CHUNKS)
        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        hits = rank(question, ids, texts, k=profile["k"])
        answer_text, status, cited, scores = extractive_answer(hits, profile["min_score"])
        band = confidence_band(scores) if status == "answered" else "Low"
        ms = (datetime.now(timezone.utc) - t0).total_seconds() * 1000
        qid = uuid.uuid4().hex[:12]
        aid = uuid.uuid4().hex[:12]
        append_row(QUERIES, [qid, now_iso(), question, "42", profile_name, str(profile["k"])])
        append_row(
            ANSWERS,
            [aid, qid, status, band, answer_text, ",".join(cited), f"{ms:.1f}"],
        )
        chips = "".join(
            f'<a class="chip" href="{url_for("chunk_view", chunk_id=cid)}">{escape(cid)}</a>' for cid in cited
        )
        top_score = f"{scores[0]:.3f}" if scores else "—"
        cls = "warn" if status == "abstained" else "ok"
        result_html = f"""
        <div class="panel">
          <div class="banner"><strong>Stub LLM</strong> — extractive only, no generative model. Draft with provenance; not auto-final.</div>
          <p class="{cls}"><strong>Status:</strong> {escape(status)} · <strong>Confidence:</strong> {escape(band)} · top score {escape(top_score)} · {ms:.0f} ms · profile {escape(profile_name)}</p>
          <div class="answer-body">{escape(answer_text)}</div>
          <div class="chips">{chips if chips else '<span class="muted">No citation chips (abstained).</span>'}</div>
        </div>
        """

    body = f"""
    <section class="panel">
      <h2>Ask the packet corpus</h2>
      <p class="muted">Municipal research questions only work after packets are ingested. Answers are extractive sentences with citation chips.</p>
      <form method="post">
        <label>Question</label>
        <input type="text" name="question" required placeholder="What was the roll-call vote on Ordinance 2024-07?" value="{escape(request.form.get('question') or '')}" />
        <label>Threshold profile</label>
        <select name="profile">
          <option value="strict">strict</option>
          <option value="balanced" selected>balanced</option>
          <option value="exploratory">exploratory</option>
        </select>
        <p style="margin-top:0.8rem"><input type="submit" value="Ask ClerkLens" /></p>
      </form>
    </section>
    {result_html}
    """
    return page("Ask", "ask", body)


@app.get("/history")
def history():
    queries = {q["query_id"]: q for q in read_rows(QUERIES)}
    rows_html = []
    for a in reversed(read_rows(ANSWERS)):
        q = queries.get(a["query_id"], {})
        chips = "".join(
            f'<a class="chip" href="{url_for("chunk_view", chunk_id=cid.strip())}">{escape(cid.strip())}</a>'
            for cid in (a.get("cited_chunk_ids") or "").split(",")
            if cid.strip()
        )
        rows_html.append(
            f"<tr><td>{escape(q.get('asked_at',''))}</td><td>{escape(q.get('question',''))}</td>"
            f"<td>{escape(a.get('status',''))} / {escape(a.get('confidence_band',''))}</td>"
            f"<td>{escape(a.get('answer_text',''))}<div class='chips'>{chips}</div></td></tr>"
        )
    body = f"""
    <section class="panel">
      <h2>Question history</h2>
      <p class="muted">Persisted in CSV — survives server restart.</p>
      <table>
        <thead><tr><th>When</th><th>Question</th><th>Status</th><th>Answer</th></tr></thead>
        <tbody>{''.join(rows_html) or '<tr><td colspan=4 class="muted">No questions yet.</td></tr>'}</tbody>
      </table>
    </section>
    """
    return page("History", "history", body)


@app.get("/chunk/<chunk_id>")
def chunk_view(chunk_id: str):
    row = next((c for c in read_rows(CHUNKS) if c["chunk_id"] == chunk_id), None)
    if not row:
        abort(404, "Chunk not found")
    doc = next((d for d in read_rows(DOCS) if d["doc_id"] == row["doc_id"]), {})
    body = f"""
    <section class="panel">
      <h2>Source chunk <code>{escape(chunk_id)}</code></h2>
      <p class="muted">From {escape(doc.get('filename', row['doc_id']))} ({escape(doc.get('doc_type',''))})</p>
      <div class="evidence"><mark>{escape(row['text'])}</mark></div>
      <p style="margin-top:0.8rem"><a class="btn secondary" href="{url_for('ask')}">Back to Ask</a></p>
    </section>
    """
    return page(f"Chunk {chunk_id}", "ask", body)


if __name__ == "__main__":
    # Prefer 5055 to avoid colliding with other local demos; still open this URL.
    import os

    port = int(os.environ.get("CLERKLENS_PORT", "5055"))
    print(f"ClerkLens → http://127.0.0.1:{port}/")
    app.run(host="127.0.0.1", port=port, debug=False)
