"""
RAG store for policy/standard documents. Chroma handles embedding
(default embedding function) and similarity search — swap
`chromadb.PersistentClient` for your existing vector DB if you already
run one (pgvector, Qdrant, etc.); only this file would need to change.
"""

import os
import sys
import glob
from pathlib import Path

import chromadb
import requests
from chromadb import Documents, EmbeddingFunction, Embeddings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CHROMA_PATH, COLLECTIONS, POLICIES_ROOT, RAG_TOP_K, EMBEDDING_MODEL, OLLAMA_HOST


class OllamaEmbeddingFunction(EmbeddingFunction):
    """
    Embeds via Ollama's /api/embeddings endpoint instead of Chroma's default
    (which downloads a model from Hugging Face on first use). Keeps the
    whole RAG stack local, consistent with running everything through Ollama.
    Requires `ollama pull nomic-embed-text` (or set a different EMBEDDING_MODEL).
    """

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            resp = requests.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json={"model": EMBEDDING_MODEL, "prompt": text},
                timeout=60,
            )
            resp.raise_for_status()
            embeddings.append(resp.json()["embedding"])
        return embeddings


def _get_collection(collection_key: str):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=COLLECTIONS[collection_key],
        embedding_function=OllamaEmbeddingFunction(),
    )


def _get_standards_collection():
    return _get_collection("standards")


def _get_master_policies_collection():
    return _get_collection("master_policies")


def _read_text_file(filepath: str) -> str:
    try:
        return Path(filepath).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(filepath).read_text(encoding="cp1252", errors="replace")


def ingest_policies(policies_dir: str, collection_key: str = "standards"):
    """
    Chunk and load every .txt/.md file in policies_dir into the vector
    store. Call this once at setup and again whenever policies change —
    it's idempotent (re-adding the same id overwrites).
    """
    collection = _get_collection(collection_key)
    files = glob.glob(os.path.join(policies_dir, "*.txt")) + \
        glob.glob(os.path.join(policies_dir, "*.md"))

    for filepath in files:
        text = _read_text_file(filepath)

        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        fname = os.path.basename(filepath)

        collection.add(
            documents=chunks,
            ids=[f"{fname}::{i}" for i in range(len(chunks))],
            metadatas=[{"source": fname} for _ in chunks],
        )

    print(f"Ingested {len(files)} policy file(s) into '{COLLECTIONS[collection_key]}'.")


def retrieve_policy_context(query: str, collection_key: str = "standards", top_k: int = RAG_TOP_K) -> list[dict]:
    """Returns a list of {text, source} dicts for the top-k matching chunks."""
    collection = _get_collection(collection_key)
    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=top_k)
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    return [
        {"text": doc, "source": meta.get("source", "unknown")}
        for doc, meta in zip(docs, metas)
    ]


if __name__ == "__main__":
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ingest_policies(os.path.join(repo_root, POLICIES_ROOT, "standards"), collection_key="standards")
    ingest_policies(os.path.join(repo_root, POLICIES_ROOT, "master_policies"), collection_key="master_policies")
