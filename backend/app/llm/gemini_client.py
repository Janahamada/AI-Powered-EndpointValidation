"""Gemini API wrapper for chat generation and embeddings.

This module replaces the old local-model path while keeping the rest of the
application compatible with the same call shape.
"""

from __future__ import annotations

import time
from typing import Iterable

import requests
from sentence_transformers import SentenceTransformer

from app.config import settings


class GeminiUnavailable(RuntimeError):
    """Raised when the Gemini API is unreachable or rejects a request."""


_LIVENESS_TTL_SECONDS = 30.0
_liveness = {"ts": 0.0, "up": False}
_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def _api_base() -> str:
    return "https://generativelanguage.googleapis.com/v1beta"


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
    }



def is_gemini_enabled() -> bool:
    """Return whether Gemini is configured and AI mode is enabled."""
    return bool(settings.AI_ENABLED and settings.GEMINI_API_KEY)


def is_gemini_up(force: bool = False) -> bool:
    """Return whether Gemini is currently usable."""
    if not is_gemini_enabled():
        return False

    now = time.time()
    if not force and (now - _liveness["ts"]) < _LIVENESS_TTL_SECONDS:
        return _liveness["up"]

    payload = {
        "contents": [{"parts": [{"text": "ping"}]}],
        "generationConfig": {"maxOutputTokens": 4},
    }

    try:
        resp = requests.post(
            f"{_api_base()}/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}",
            json=payload,
            headers=_headers(),
            timeout=10,
        )

        if not resp.ok:
            print("Gemini health check failed")
            print("Status:", resp.status_code)
            print("Body:", resp.text)

        resp.raise_for_status()
        up = True

    except requests.RequestException:
        up = False

    _liveness.update(ts=now, up=up)
    return up


def call_gemini(
    model: str,
    system: str,
    prompt: str,
    json_mode: bool = False,
    temperature: float = 0.2,
    timeout: int | None = None,
) -> str:
    """Call Gemini's generateContent endpoint and return the response text."""

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": system,
                }
            ]
        },
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 2048,
        },
    }

    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    url = (
        f"{_api_base()}/models/{model}:generateContent"
        f"?key={settings.GEMINI_API_KEY}"
    )

    try:
        resp = requests.post(
            url,
            json=payload,
            headers=_headers(),
            timeout=timeout or settings.GEMINI_TIMEOUT,
        )

        # Always print the raw response while debugging
        print("=" * 80)
        print("Gemini URL:", url)
        print("Status:", resp.status_code)
        print("Response:")
        print(resp.text)
        print("=" * 80)

        resp.raise_for_status()

    except requests.RequestException as e:
        _liveness.update(ts=time.time(), up=False)

        raise GeminiUnavailable(
            f"Gemini call failed for model '{model}'. "
            f"HTTP {getattr(resp, 'status_code', 'Unknown')}.\n"
            f"Response:\n{getattr(resp, 'text', '')}"
        ) from e

    try:
        data = resp.json()

        candidates = data.get("candidates")
        if not candidates:
            raise GeminiUnavailable(
                f"No candidates returned.\nFull response:\n{resp.text}"
            )

        parts = candidates[0]["content"]["parts"]
        if not parts:
            raise GeminiUnavailable(
                f"No content parts returned.\nFull response:\n{resp.text}"
            )

        text = parts[0]["text"]

    except Exception as exc:
        _liveness.update(ts=time.time(), up=False)
        raise GeminiUnavailable(
            f"Unexpected Gemini response.\nFull response:\n{resp.text}"
        ) from exc

    _liveness.update(ts=time.time(), up=True)
    return text


def embed_text(text: str, model: str | None = None) -> list[float]:
    return _embedding_model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).tolist()


def embed_texts(
    texts: Iterable[str],
    model: str | None = None,
) -> list[list[float]]:
    return _embedding_model.encode(
        list(texts),
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).tolist()

# Compatibility aliases
is_ollama_up = is_gemini_up
call_ollama = call_gemini