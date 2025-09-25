#!/usr/bin/env python3
"""
hybrid_retriever.py

Re-rank TF-IDF candidate passages using semantic embeddings.

API:
 - rerank_candidates(query: str, candidates: List[Tuple[index, score, passage]], top_k=3, model_name=None)

If sentence-transformers is not installed, this module will return the original
TF-IDF ranking (graceful fallback).
"""
from typing import List, Tuple, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


def rerank_candidates(query: str, candidates: List[Tuple[int, float, str]], top_k: int = 3, model_name: Optional[str] = None):
    """Return top_k candidates re-ranked by cosine similarity of embeddings.

    candidates: list of (index, score, passage)
    """
    if SentenceTransformer is None:
        # fallback: return top_k of input as-is
        return candidates[:top_k]

    model_name = model_name or 'all-MiniLM-L6-v2'
    # force CPU device for stability
    model = SentenceTransformer(model_name, device='cpu')

    passages = [p[2] for p in candidates]
    # compute embeddings
    emb_pass = model.encode(passages, convert_to_numpy=True)
    emb_q = model.encode([query], convert_to_numpy=True)[0]

    # cosine similarities
    # normalize
    def normalize(x):
        denom = np.linalg.norm(x, axis=1, keepdims=True)
        denom[denom == 0] = 1e-8
        return x / denom

    emb_pass_n = normalize(emb_pass)
    emb_q_n = emb_q / (np.linalg.norm(emb_q) + 1e-8)

    sims = np.dot(emb_pass_n, emb_q_n)
    idxs = np.argsort(sims)[::-1][:top_k]

    reranked = [(candidates[int(i)][0], float(sims[i]), candidates[int(i)][2]) for i in idxs]
    return reranked


if __name__ == '__main__':
    # simple demo
    print('Hybrid reranker demo')
    q = input('query: ')
    # sample candidates
    c = [(0, 0.1, 'A sleepy water spirit. When TIRED, use Ralsei\'s PACIFY!'),
         (1, 0.05, 'Ralsei encourages you to get hit by the ambulances.'),
         (2, 0.02, 'The hymn of the prophecy.')]
    out = rerank_candidates(q, c, top_k=3)
    for item in out:
        print(item)
