from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DEPARTMENT_ACCESS: dict[str, set[str]] = {
    "engineering": {"admin", "ceo", "leadership", "engineering_lead", "tech_lead", "engineering"},
    "finance": {"admin", "ceo", "leadership", "finance_lead", "finance"},
    "hr": {"admin", "ceo", "leadership", "hr_lead", "hr"},
    "marketing": {"admin", "ceo", "leadership", "sales", "marketing", "all_employees"},
    "general": {"admin", "ceo", "leadership", "all_employees"},
}

PRIVILEGED_ROLES = {"admin", "ceo", "leadership"}
_ROLE_RETRIEVAL_CACHE: dict[str, dict[str, Any]] = {}


def normalize_query(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _resolve_chunks_csv() -> Path:
    candidates = [
        Path.cwd() / "artifacts" / "module2" / "chunks" / "cleaned_formatted_chunks.csv",
        Path.cwd().parent / "artifacts" / "module2" / "chunks" / "cleaned_formatted_chunks.csv",
    ]
    for item in candidates:
        if item.exists():
            return item
    raise FileNotFoundError("Could not find artifacts/module2/chunks/cleaned_formatted_chunks.csv")


@lru_cache(maxsize=1)
def _load_chunks() -> list[dict[str, Any]]:
    df = pd.read_csv(_resolve_chunks_csv())
    records = df.to_dict("records")
    for row in records:
        roles = row.get("accessible_roles", "")
        if isinstance(roles, str):
            row["accessible_roles"] = [r.strip() for r in roles.split(",") if r.strip()]
        else:
            row["accessible_roles"] = []
    return records


def _filter_chunks_by_role(role: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for chunk in chunks:
        dept = str(chunk.get("department", "")).lower()
        allowed_roles = DEPARTMENT_ACCESS.get(dept, set())
        if role not in allowed_roles:
            continue
        if role in PRIVILEGED_ROLES:
            filtered.append(chunk)
            continue
        chunk_roles = chunk.get("accessible_roles", [])
        if not chunk_roles or role in chunk_roles:
            filtered.append(chunk)
    return filtered


def _retrieve_for_role(role: str, query: str, chunks: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    if not chunks:
        return []

    cache_key = f"role:{role}:n:{len(chunks)}"
    cached = _ROLE_RETRIEVAL_CACHE.get(cache_key)

    if cached is None:
        docs = [normalize_query(str(c.get("content", ""))) for c in chunks]
        vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(docs)
        cached = {"vectorizer": vectorizer, "matrix": matrix, "chunks": chunks}
        _ROLE_RETRIEVAL_CACHE[cache_key] = cached

    q = normalize_query(query)
    q_vec = cached["vectorizer"].transform([q])
    sims = cosine_similarity(q_vec, cached["matrix"])[0]

    idxs = sims.argsort()[::-1][:top_k]
    output: list[dict[str, Any]] = []
    for idx in idxs:
        obj = dict(cached["chunks"][idx])
        obj["retrieval_score"] = float(sims[idx])
        output.append(obj)
    return output


def _confidence(retrieved: list[dict[str, Any]]) -> float:
    if not retrieved:
        return 0.0
    scores = [max(0.0, min(1.0, float(x.get("retrieval_score", 0.0)))) for x in retrieved]
    top = scores[0]
    mean_top3 = sum(scores[:3]) / min(3, len(scores))
    return round(0.65 * top + 0.35 * mean_top3, 4)


def _openai_generate(question: str, context: str) -> str:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("OPENAI_API_KEY is not set")
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {
                "role": "system",
                "content": "Answer only using context. Cite sources like [chunk_id | source_document | department].",
            },
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"},
        ],
        "temperature": 0.1,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    resp = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=45)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _gemini_generate(question: str, context: str) -> str:
    # Backward-compatible lookup: if user accidentally stored Gemini key in OPENAI_API_KEY,
    # this still works.
    key = os.getenv("GEMINI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set")

    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are a grounded assistant. Use only provided context. "
                            "Cite sources like [chunk_id | source_document | department].\n\n"
                            f"Question: {question}\n\nContext:\n{context}"
                        )
                    }
                ]
            }
        ],
        "generationConfig": {"temperature": 0.1},
    }

    resp = requests.post(url, params={"key": key}, json=payload, headers=headers, timeout=45)
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("No response candidates returned by Gemini")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise ValueError("Gemini response was empty")
    return text


def _mock_generate(retrieved: list[dict[str, Any]]) -> str:
    if not retrieved:
        return "I do not have enough information in the accessible documents to answer this question."
    top = retrieved[0]
    preview = str(top.get("content", "")).replace("\n", " ")[:450]
    return (
        "Based on the top retrieved context, "
        f"{preview} ... [{top.get('chunk_id')} | {top.get('source_document')} | {top.get('department')}]"
    )


def run_rag_query(username: str, role: str, question: str, top_k: int = 5) -> dict[str, Any]:
    all_chunks = _load_chunks()
    allowed = _filter_chunks_by_role(role, all_chunks)
    retrieved = _retrieve_for_role(role, question, allowed, top_k=max(1, min(10, top_k)))

    context_lines = []
    for c in retrieved:
        context_lines.append(
            f"chunk_id={c.get('chunk_id')} | source={c.get('source_document')} | dept={c.get('department')}\n{str(c.get('content', ''))[:1200]}"
        )
    context = "\n\n".join(context_lines)

    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "openai":
        try:
            answer = _openai_generate(question, context)
        except Exception:
            answer = _mock_generate(retrieved)
    elif provider == "gemini":
        try:
            answer = _gemini_generate(question, context)
        except Exception:
            answer = _mock_generate(retrieved)
    else:
        answer = _mock_generate(retrieved)

    sources = [
        {
            "chunk_id": c.get("chunk_id"),
            "source_document": c.get("source_document"),
            "department": c.get("department"),
            "retrieval_score": round(float(c.get("retrieval_score", 0.0)), 4),
            "snippet": str(c.get("content", ""))[:240].replace("\n", " "),
        }
        for c in retrieved
    ]

    return {
        "user": username,
        "role": role,
        "query": question,
        "answer": answer,
        "confidence": _confidence(retrieved),
        "sources": sources,
        "retrieved_count": len(retrieved),
    }


def accessible_departments_for_role(role: str) -> list[str]:
    return sorted([dept for dept, roles in DEPARTMENT_ACCESS.items() if role in roles])
