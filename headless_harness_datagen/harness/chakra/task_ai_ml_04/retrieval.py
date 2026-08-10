"""Pure-Python TF-IDF + cosine retrieval (no scikit-learn)."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

TOKEN_RE = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall((text or "").lower())


def tfidf_matrix(docs: list[str]) -> tuple[list[dict[str, float]], dict[str, float]]:
    tokenized = [tokenize(d) for d in docs]
    df: Counter[str] = Counter()
    for toks in tokenized:
        df.update(set(toks))
    n = len(docs) or 1
    idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}
    vectors: list[dict[str, float]] = []
    for toks in tokenized:
        tf = Counter(toks)
        length = len(toks) or 1
        vec = {t: (tf[t] / length) * idf[t] for t in tf}
        vectors.append(vec)
    return vectors, idf


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def rank(
    question: str,
    chunk_ids: list[str],
    texts: list[str],
    k: int = 4,
) -> list[tuple[str, str, float]]:
    if not texts:
        return []
    vectors, idf = tfidf_matrix(texts + [question])
    q_vec = vectors[-1]
    doc_vecs = vectors[:-1]
    scored: list[tuple[str, str, float]] = []
    for i, vec in enumerate(doc_vecs):
        scored.append((chunk_ids[i], texts[i], cosine(q_vec, vec)))
    scored.sort(key=lambda x: (-x[2], x[0]))
    return scored[:k]


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def extractive_answer(
    hits: list[tuple[str, str, float]],
    min_score: float,
) -> tuple[str, str, list[str], list[float]]:
    """Returns answer_html_safe_text, status, cited_ids, scores."""
    if not hits or hits[0][2] < min_score:
        return (
            "Abstaining — retrieval confidence is below the profile threshold. "
            "No extractive answer will be invented for this question.",
            "abstained",
            [],
            [h[2] for h in hits],
        )
    cited: list[str] = []
    scores: list[float] = []
    lines: list[str] = []
    for cid, text, score in hits:
        if score < min_score * 0.85:
            continue
        cited.append(cid)
        scores.append(score)
        # Prefer a sentence that overlaps the chunk well
        sents = sentences(text)
        pick = sents[0] if sents else text[:220]
        lines.append(f"{pick} [{cid}]")
    if not lines:
        return (
            "Abstaining — no chunk cleared the confidence floor.",
            "abstained",
            [],
            [h[2] for h in hits],
        )
    band = confidence_band(scores)
    body = " ".join(lines)
    return body, "answered", cited, scores


def confidence_band(scores: Iterable[float]) -> str:
    scores = list(scores)
    if not scores:
        return "Low"
    top = scores[0]
    margin = top - (scores[1] if len(scores) > 1 else 0.0)
    if top >= 0.22 and margin >= 0.04:
        return "High"
    if top >= 0.12:
        return "Medium"
    return "Low"


PROFILES = {
    "strict": {"k": 3, "min_score": 0.14},
    "balanced": {"k": 4, "min_score": 0.08},
    "exploratory": {"k": 5, "min_score": 0.04},
}
