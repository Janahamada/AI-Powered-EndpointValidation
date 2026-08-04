"""RAG store for policy/standard documents, backed by Chroma."""

import glob
import os
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings


def _chromadb():
    import chromadb
    return chromadb


class _SimpleEmbeddingFunction:
    """
    Uses the embedding model configured by embed_texts().
    """

    def _embed(self, input):
        from app.llm.gemini_client import embed_texts

        texts = [input] if isinstance(input, str) else list(input)

        embeddings = embed_texts(texts)

        # Convert numpy/torch objects to Python lists
        if hasattr(embeddings, "tolist"):
            embeddings = embeddings.tolist()

        return embeddings

    def __call__(self, input):
        return self._embed(input)

    def embed_documents(self, input):
        return self._embed(input)

    def embed_query(self, input):
        return self._embed(input)

    def name(self):
        return settings.EMBEDDING_MODEL


def _get_collection(collection_key: str):
    client = _chromadb().PersistentClient(path=settings.CHROMA_PATH)

    return client.get_or_create_collection(
        name=settings.collections[collection_key],
        embedding_function=_SimpleEmbeddingFunction(),
    )


def _read_text_file(filepath: str):
    try:
        return Path(filepath).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(filepath).read_text(
            encoding="cp1252",
            errors="replace",
        )


def _chunk_text(text: str):
    """
    Paragraph chunking.
    Every paragraph becomes one chunk.
    Empty paragraphs are ignored.
    Duplicate paragraphs are removed.
    """

    text = re.sub(r"\n{3,}", "\n\n", text)

    chunks = []
    seen = set()

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if paragraph in seen:
            continue

        seen.add(paragraph)
        chunks.append(paragraph)

    return chunks


def _extract_policy_id(paragraph: str) -> str | None:
    """Extract a canonical policy identifier from a paragraph."""
    # Master policy style: Policy AV-01: ...
    m = re.match(r"Policy\s+([A-Z0-9-]+)\b", paragraph)
    if m:
        return m.group(1)

    # CIS style: CIS Control 10: ... or CIS Safeguard 10.1: ...
    m = re.match(r"CIS\s+(?:Control|Safeguard)\s+([0-9.]+)\b", paragraph)
    if m:
        return m.group(1)

    # Fallback: use the filename as policy id if no policy header found.
    return None


def ingest_policies(
    policies_dir: str,
    collection_key: str = "standards",
):
    collection = _get_collection(collection_key)

    files = glob.glob(os.path.join(policies_dir, "*.txt"))
    files += glob.glob(os.path.join(policies_dir, "*.md"))

    total_chunks = 0

    for filepath in files:

        fname = os.path.basename(filepath)

        # Remove previous version of this file
        try:
            collection.delete(where={"source": fname})
        except Exception:
            pass

        text = _read_text_file(filepath)

        chunks = _chunk_text(text)

        if not chunks:
            continue

        policy_id = None
        for paragraph in text.split("\n\n"):
            if not policy_id:
                policy_id = _extract_policy_id(paragraph)

        collection.add(
            documents=chunks,
            ids=[
                f"{fname}::{i}"
                for i in range(len(chunks))
            ],
            metadatas=[
                {
                    "source": fname,
                    "policy": policy_id or fname,
                    "chunk": i,
                }
                for i in range(len(chunks))
            ],
        )

        total_chunks += len(chunks)

        if settings.RAG_DEBUG:
            print(f"Ingested {fname}: {len(chunks)} chunks")

    if settings.RAG_DEBUG:
        print(
            f"\nFinished ingestion: {len(files)} files, {total_chunks} chunks"
        )

    return len(files)


def retrieve_policy_context(
    query: str,
    collection_key: str = "standards",
    top_k: int | None = None,
):
    """
    Retrieve policy chunks.

    We intentionally ask Chroma for more than top_k,
    then filter weak matches ourselves.
    """

    top_k = top_k or settings.RAG_TOP_K

    try:

        collection = _get_collection(collection_key)

        if collection.count() == 0:

            if settings.RAG_DEBUG:
                print(f"Collection '{collection_key}' is empty.")

            return []

        if settings.RAG_DEBUG:
            print("\n==========================")
            print("RAG QUERY")
            print(query)
            print("==========================")

        results = collection.query(
            query_texts=[query],
            n_results=max(top_k * 3, 10),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

    except Exception as e:

        if settings.RAG_DEBUG:
            print("Retriever exception:", e)

        return []

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved = []

    for doc, meta, distance in zip(docs, metas, distances):

        if settings.RAG_DEBUG:
            print(
                f"{distance:.3f} | {(meta or {}).get('source')} | "
                f"{doc[:80].replace(chr(10),' ')}..."
            )

        retrieved.append(
            {
                "text": doc,
                "source": (meta or {}).get("source", "unknown"),
                "policy": (meta or {}).get("policy", "unknown"),
                "score": distance,
            }
        )

    # Lowest distance = best
    retrieved.sort(key=lambda x: x["score"])

    return retrieved[:top_k]