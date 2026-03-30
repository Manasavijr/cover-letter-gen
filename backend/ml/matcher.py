"""FAISS semantic matching — finds resume content most relevant to JD."""
import logging
import re
from typing import List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.app.core.config import settings

logger = logging.getLogger(__name__)
_model: SentenceTransformer = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def chunk_text(text: str, min_len: int = 20, max_len: int = 300) -> List[str]:
    """Split text into meaningful chunks for embedding."""
    chunks = []
    for sent in re.split(r"[.\n!;]", text):
        sent = sent.strip()
        if min_len < len(sent) < max_len:
            chunks.append(sent)
    return chunks or [text[:500]]


def find_top_matches(jd_text: str, resume_text: str, top_k: int = None) -> List[dict]:
    """
    Find resume chunks most semantically relevant to JD requirements.
    Returns top_k matches with similarity scores.
    """
    if top_k is None:
        top_k = settings.TOP_K_MATCHES

    model = get_model()
    resume_chunks = chunk_text(resume_text)
    jd_chunks = chunk_text(jd_text)

    if not resume_chunks or not jd_chunks:
        return []

    # Embed resume chunks
    resume_embs = model.encode(resume_chunks, convert_to_numpy=True, show_progress_bar=False)
    resume_embs = resume_embs / np.linalg.norm(resume_embs, axis=1, keepdims=True)

    # Build FAISS index
    index = faiss.IndexFlatIP(resume_embs.shape[1])
    index.add(resume_embs.astype(np.float32))

    # Embed JD and search
    jd_embs = model.encode(jd_chunks, convert_to_numpy=True, show_progress_bar=False)
    jd_embs = jd_embs / np.linalg.norm(jd_embs, axis=1, keepdims=True)

    scores, indices = index.search(jd_embs.astype(np.float32), k=min(3, len(resume_chunks)))

    # Collect top unique matches
    seen = set()
    matches = []
    for i in range(len(jd_chunks)):
        for j in range(scores.shape[1]):
            idx = int(indices[i, j])
            score = float(scores[i, j])
            if idx not in seen and score > 0.3:
                seen.add(idx)
                matches.append({
                    "resume_chunk": resume_chunks[idx],
                    "jd_requirement": jd_chunks[i],
                    "score": round(score, 3),
                })
    matches.sort(key=lambda x: -x["score"])
    return matches[:top_k]


def compute_match_score(jd_text: str, cover_letter: str) -> float:
    """Score how well a cover letter matches the JD (0-100)."""
    model = get_model()
    jd_chunks = chunk_text(jd_text)
    cl_chunks = chunk_text(cover_letter)
    if not jd_chunks or not cl_chunks:
        return 0.0

    jd_embs = model.encode(jd_chunks, convert_to_numpy=True, show_progress_bar=False)
    cl_embs = model.encode(cl_chunks, convert_to_numpy=True, show_progress_bar=False)

    jd_embs = jd_embs / np.linalg.norm(jd_embs, axis=1, keepdims=True)
    cl_embs = cl_embs / np.linalg.norm(cl_embs, axis=1, keepdims=True)

    index = faiss.IndexFlatIP(cl_embs.shape[1])
    index.add(cl_embs.astype(np.float32))

    scores, _ = index.search(jd_embs.astype(np.float32), k=1)
    avg_score = float(np.mean(scores[:, 0]))
    return round(min(100, avg_score * 130), 1)  # scale to 0-100
