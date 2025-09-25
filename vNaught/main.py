#!/usr/bin/env python3
import os
# Force CPU-only to avoid CUDA initialization issues early in the process
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
os.environ.setdefault('TRANSFORMERS_VERBOSITY', 'error')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')

from chatbox import ChatboxRenderer
import sys
import time

# optional components for RAG
try:
    from scripts.retriever import build_default_retriever
except Exception:
    build_default_retriever = None

try:
    from llm import get_default_llm
except Exception:
    get_default_llm = None

try:
    from scripts.hybrid_retriever import rerank_candidates
except Exception:
    rerank_candidates = None


def build_rag_prompt(question: str, contexts: list) -> str:
    # simple prompt: provide contexts then ask the question
    ctx_text = "\n\n---\n".join([f"(score:{c[1]:.3f}) {c[2]}" for c in contexts])
    prompt = (
        "Use the following extracted passages from the Deltarune wiki to answer the user's question. "
        "When uncertain, be honest and cite the passages.\n\nPassages:\n"
        f"{ctx_text}\n\nQuestion: {question}\nAnswer:"
    )
    return prompt


def main():
    chatbox = ChatboxRenderer()

    welcome_message = "Hi! I'm Ralsei! I'm here to chat with you and be your friend! (Press Ctrl+C to exit)"
    chatbox.display(welcome_message, "happy")

    # try to instantiate optional RAG components
    retriever = None
    llm = None
    if build_default_retriever is not None:
        try:
            retriever = build_default_retriever()
        except Exception as e:
            print('Warning: retriever not available:', e)

    if get_default_llm is not None:
        try:
            llm = get_default_llm()
        except Exception as e:
            print('Warning: LLM wrapper not available:', e)

    try:
        while True:
            user_input = input("\nYou: ")

            # if we have a retriever and llm, do RAG
            response = None
            emotion = 'neutral'

            if retriever is not None and llm is not None:
                try:
                    # get larger candidate set from TF-IDF then re-rank with embeddings
                    tfidf_candidates = retriever.retrieve(user_input, k=50)
                    if rerank_candidates is not None:
                        contexts = rerank_candidates(user_input, tfidf_candidates, top_k=3)
                    else:
                        contexts = tfidf_candidates[:3]

                    prompt = build_rag_prompt(user_input, contexts)
                    generated = llm.generate(prompt, max_tokens=256)
                    response = generated
                    emotion = 'happy'
                except Exception as e:
                    response = f"[RAG error] {e}"
                    emotion = 'surprised'

            # fallback simple reply
            if response is None:
                response = "That's interesting! I'm looking forward to when I can respond more meaningfully!"

            time.sleep(0.5)
            chatbox.display(response, emotion)

    except KeyboardInterrupt:
        chatbox.display("Goodbye! It was nice talking to you!", "sad")
        time.sleep(1)
        sys.exit(0)


if __name__ == "__main__":
    main()