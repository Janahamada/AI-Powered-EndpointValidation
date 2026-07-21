"""
Thin wrapper around Ollama's REST API. Kept separate from extraction.py
and recommendation.py so retries, timeouts, and error handling live in
one place.
"""

import json
import requests

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OLLAMA_HOST


def call_ollama(
    model: str,
    system: str,
    prompt: str,
    json_mode: bool = False,
    temperature: float = 0.2,
    timeout: int = 60,
) -> str:
    """
    Calls Ollama's /api/chat endpoint. Returns the raw text of the response.
    json_mode=True asks Ollama to constrain output to valid JSON — still
    validate/parse defensively, constrained decoding reduces malformed
    output, it doesn't guarantee semantically correct output.
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
            f"{OLLAMA_HOST}/api/chat", json=payload, timeout=timeout
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Ollama call failed for model {model}: {e}") from e

    data = resp.json()
    return data["message"]["content"]
