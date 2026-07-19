"""
Thin wrapper around Ollama's REST API. Kept separate from extraction.py
and recommendation.py so retries, timeouts, and error handling live in
one place.
"""