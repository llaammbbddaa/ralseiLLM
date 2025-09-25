#!/usr/bin/env python3
"""
retriever.py

Simple TF-IDF based retriever for local RAG experiments.

Functions:
 - build_index(text_path, chunk_size, overlap): loads and chunks a text file
 - retrieve(query, k): returns top-k passages for a query

This is lightweight and depends on scikit-learn. If scikit-learn is not
installed, the module will still import but raise a clear error when used.
"""
from typing import List, Tuple
import os
import math

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception as e:
    TfidfVectorizer = None
    cosine_similarity = None


class Retriever:
    def __init__(self, text_path: str, chunk_size: int = 400, overlap: int = 100):
        self.text_path = text_path
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.passages: List[str] = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self._build_index()

    def _load_text(self) -> str:
        with open(self.text_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _chunk_text(self, text: str) -> List[str]:
        # naive chunking by characters preserving overlap
        passages = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + self.chunk_size
            passages.append(text[start:end].strip())
            if end >= text_len:
                break
            start = end - self.overlap
        return [p for p in passages if p]

    def _build_index(self):
        if TfidfVectorizer is None:
            raise ImportError("scikit-learn is required for the retriever. Install with: pip install scikit-learn")

        text = self._load_text()
        self.passages = self._chunk_text(text)

        # use TF-IDF with simple preprocessing
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(self.passages)

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[int, float, str]]:
        """Return list of (index, score, passage) sorted by score desc."""
        if self.tfidf_matrix is None:
            raise RuntimeError("Index not built")
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.tfidf_matrix)[0]
        idxs = sims.argsort()[::-1][:k]
        return [(int(i), float(sims[i]), self.passages[i]) for i in idxs]


def build_default_retriever():
    base = os.path.dirname(os.path.dirname(__file__))
    text_path = os.path.join(base, 'wikiStuff', 'deltarune_wiki_data.txt')
    return Retriever(text_path)


if __name__ == '__main__':
    # simple demo
    try:
        r = build_default_retriever()
    except Exception as e:
        print('Error building retriever:', e)
        raise
    query = input('query: ')
    for i, score, passage in r.retrieve(query, k=5):
        print(f'[{i}] {score:.3f} {passage[:200].replace("\n"," ")}')
