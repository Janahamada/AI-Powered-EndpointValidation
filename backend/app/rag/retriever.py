"""
RAG store for policy/standard documents, backed by Chroma with embeddings
served locally by Ollama (nomic-embed-text).

chromadb and Ollama are BOTH optional at runtime: every entry point here is
wrapped so that a missing chromadb install or an unreachable Ollama server
degrades to "no context retrieved" rather than raising. This keeps the API
booting and answering (deterministically) with zero AI infrastructure.
"""

import glob
import os
import sys
from pathlib import Path

import requests

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings


def _chromadb():
    """Import chromadb lazily so the package is optional."""
    import chromadb  # noqa: PLC0415

    return chromadb


class _OllamaEmbeddingFunction:
    """Embeds via Ollama's /api/embeddings endpoint. Implemented duck-typed so
    we don't import chromadb's base class at module load.

    Supports both the legacy chromadb interface (a single ``__call__``) and the
    chromadb >=1.0 interface (separate ``embed_documents`` / ``embed_query``),
    all delegating to the same Ollama embedding call so documents and queries
    share one embedding space."""

    def _embed(self, input) -> list:  # noqa: A002 - chroma's required signature
        texts = [input] if isinstance(input, str) else list(input)
        embeddings = []
        for text in texts:
            resp = requests.post(
                f"{settings.OLLAMA_HOST}/api/embeddings",
                json={"model": settings.EMBEDDING_MODEL, "prompt": text},
                timeout=settings.OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            embeddings.append(resp.json()["embedding"])
        return embeddings

    # Legacy chromadb (<1.0) calls the function directly.
    def __call__(self, input):  # noqa: A002
        return self._embed(input)

    # chromadb >=1.0 calls these explicitly.
    def embed_documents(self, input):  # noqa: A002
        return self._embed(input)

    def embed_query(self, input):  # noqa: A002
        return self._embed(input)

    def name(self) -> str:
        return "ollama-nomic-embed-text"


def _get_collection(collection_key: str):
    client = _chromadb().PersistentClient(path=settings.CHROMA_PATH)
    return client.get_or_create_collection(
        name=settings.collections[collection_key],
        embedding_function=_OllamaEmbeddingFunction(),
    )


def _read_text_file(filepath: str) -> str:
    try:
        return Path(filepath).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(filepath).read_text(encoding="cp1252", errors="replace")


def ingest_policies(policies_dir: str, collection_key: str = "standards") -> int:
    """Chunk and load every .txt/.md file in policies_dir into the vector
    store. Idempotent (re-adding the same id overwrites)."""
    collection = _get_collection(collection_key)
    files = glob.glob(os.path.join(policies_dir, "*.txt")) + glob.glob(
        os.path.join(policies_dir, "*.md")
    )
    for filepath in files:
        text = _read_text_file(filepath)
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        fname = os.path.basename(filepath)
        if not chunks:
            continue
        collection.add(
            documents=chunks,
            ids=[f"{fname}::{i}" for i in range(len(chunks))],
            metadatas=[{"source": fname} for _ in chunks],
        )
    return len(files)


def retrieve_policy_context(
    query: str, collection_key: str = "standards", top_k: int | None = None
) -> list[dict]:
    """Returns a list of {text, source} dicts for the top-k matching chunks.
    Returns [] on any failure (chromadb missing, store empty, Ollama down)."""
    top_k = top_k or settings.RAG_TOP_K
    try:
        collection = _get_collection(collection_key)
        if collection.count() == 0:
            return []
        results = collection.query(query_texts=[query], n_results=top_k)
    except Exception:
        # chromadb not installed, store missing, or embedding backend down.
        return []

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    return [
        {"text": doc, "source": (meta or {}).get("source", "unknown")}
        for doc, meta in zip(docs, metas)
    ]
