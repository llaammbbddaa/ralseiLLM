**a little ralsei chatbot, only the cli interface has been done so far**
<br>
**ideally i would also integrate an llm, and maybe even some rag stuff for relevant deltarune pieces**

## TODO
- integrate llm
- integrate rag

## RAG / local LLM setup

This project includes a simple TF-IDF retriever and a tiny LLM wrapper to experiment with Retrieval-Augmented Generation (RAG) locally.

Quick steps:

1. (Optional) Create a virtualenv and install optional deps:

	pip install -r requirements.txt

2. The retriever uses `wikiStuff/deltarune_wiki_data.txt` as the knowledge source.

3. Run the CLI:

	python main.py

If `scikit-learn` or `transformers` are not installed the program will still run, but will use a simple fallback responder.

Hybrid retriever (TF‑IDF → embeddings re-rank):

 - To enable semantic re-ranking, install `sentence-transformers` and an ANN backend if desired.
 - The code will request 50 TF‑IDF candidates and re-rank them with `sentence-transformers/all-MiniLM-L6-v2` when available.

