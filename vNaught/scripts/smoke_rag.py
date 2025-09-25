#!/usr/bin/env python3
"""
Lightweight smoke test for the RAG pipeline (retriever -> hybrid rerank -> llm.generate).

This script is intentionally standalone and does not use the Chatbox UI. It prints
what it does so we can iterate and fix issues before wiring into the CLI.
"""
import os
import sys
import pathlib

# ensure project root is on sys.path so `scripts.*` imports work when running this file
proj_root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(proj_root))

os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
os.environ.setdefault('TRANSFORMERS_VERBOSITY', 'error')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')

from scripts.retriever import build_default_retriever
from llm import get_default_llm
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

# toggles: set env RALSEI_ENABLE_EMBEDDINGS=1 to enable sentence-transformers reranking
# set RALSEI_USE_TRANSFORMERS=1 to allow llm to use transformers pipeline; otherwise
# the script will force the deterministic fallback (no torch import).
ENABLE_EMBEDDINGS = os.environ.get('RALSEI_ENABLE_EMBEDDINGS', '') == '1'
USE_TRANSFORMERS = os.environ.get('RALSEI_USE_TRANSFORMERS', '') == '1'

if ENABLE_EMBEDDINGS:
    # import hybrid reranker lazily (may import sentence-transformers)
    try:
        from scripts.hybrid_retriever import rerank_candidates
    except Exception as e:
        print('Could not import hybrid reranker:', e)
        rerank_candidates = None
else:
    rerank_candidates = None


def run_query(q: str):
    print('---')
    print('Query:', q)

    r = build_default_retriever()
    print('Loaded passages:', len(r.passages))

    tfidf_top = r.retrieve(q, k=10)
    print('\nTop TF-IDF candidates:')
    for i, s, p in tfidf_top[:5]:
        print(f'[{i}] score={s:.3f} {p[:200].replace("\n"," ")}')

    # try hybrid rerank
    reranked = None
    if ENABLE_EMBEDDINGS and callable(globals().get('rerank_candidates')):
        try:
            reranked = rerank_candidates(q, tfidf_top, top_k=3)
            print('\nReranked top-3:')
            for i, s, p in reranked:
                print(f'[{i}] sim={s:.3f} {p[:200].replace("\n"," ")}')
        except Exception as e:
            print('\nHybrid rerank failed (falling back):', e)

    if reranked is None:
        reranked = tfidf_top[:3]

    # build prompt and call LLM
    llm = get_default_llm()
    prompt = 'Passages:\n' + '\n---\n'.join([p for _, _, p in reranked]) + '\n\nQuestion: ' + q + '\nAnswer:'
    print('\nPrompt (first 400 chars):')
    print(prompt[:400].replace('\n','\\n'))

    print('\nCalling LLM...')
    if USE_TRANSFORMERS and llm is not None and getattr(llm, 'generator', None) is not None:
        out = llm.generate(prompt, max_tokens=128)
        print('\nLLM output:')
        print(out)
    else:
        # simple extractive fallback: choose best sentence from top passage(s)
        def extractive_answer(candidates, question):
            import re
            q_tokens = set([t.lower() for t in re.findall(r"\w+", question)])
            best = ''
            best_score = -1
            for _, _, passage in candidates:
                # split into sentences
                sents = re.split(r'[\.\n]+', passage)
                for s in sents:
                    tokens = set([t.lower() for t in re.findall(r"\w+", s)])
                    score = len(q_tokens & tokens)
                    if score > best_score and len(s.strip())>20:
                        best_score = score
                        best = s.strip()
            if not best:
                # fallback to first candidate snippet
                best = candidates[0][2][:200].replace('\n',' ')
            return best

        out = extractive_answer(reranked, q)
        print('\nFallback extractive answer:')
        print(out)


if __name__ == '__main__':
    queries = [
        'How do I pacify enemies?',
        'Who is Ralsei?',
        'What happens when you seal a Dark Fountain?'
    ]
    for q in queries:
        try:
            run_query(q)
        except Exception as e:
            print('ERROR during query:', e)
            raise
