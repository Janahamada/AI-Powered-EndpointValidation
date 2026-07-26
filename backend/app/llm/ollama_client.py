"""
Thin wrapper around Ollama's REST API. Retries, timeouts, and error
handling live in one place.

Raises `OllamaUnavailable` (a subclass of RuntimeError) when Ollama can't be
reached or returns an error, so callers can degrade to a deterministic
fallback instead of surfacing a 500.
"""

import time

import requests

from app.config import settings


class OllamaUnavailable(RuntimeError):
    """Raised when the local Ollama server is unreachable or errors out."""


# Cached liveness so that when Ollama is offline we pay the (short) probe cost
# at most once per TTL window instead of blocking on a failed connect for every
# extraction/recommendation call. This is what keeps the deterministic offline
# path fast (single request never probes more than once).
_LIVENESS_TTL_SECONDS = 15.0
_liveness = {"ts": 0.0, "up": False}


def is_ollama_up(force: bool = False) -> bool:
    """Fast, cached liveness probe. Short timeout so a down server never blocks
    a request for long; result cached for a few seconds."""
    now = time.time()
    if not force and (now - _liveness["ts"]) < _LIVENESS_TTL_SECONDS:
        return _liveness["up"]
    up = False
    try:
        resp = requests.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=1.5)
        up = resp.status_code == 200
    except requests.RequestException:
        up = False
    _liveness.update(ts=now, up=up)
    return up


def call_ollama(
    model: str,
    system: str,
    prompt: str,
    json_mode: bool = False,
    temperature: float = 0.2,
    timeout: int | None = None,
) -> str:
    """
    Calls Ollama's /api/chat endpoint and returns the raw response text.
    json_mode=True asks Ollama to constrain output to valid JSON — still
    validate/parse defensively downstream.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": temperature},
    }
    if json_mode:
        payload["format"] = "json"

    try:
        resp = requests.post(
            f"{settings.OLLAMA_HOST}/api/chat",
            json=payload,
            timeout=timeout or settings.OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise OllamaUnavailable(f"Ollama call failed for model {model}: {e}") from e

    data = resp.json()
    return data["message"]["content"]
