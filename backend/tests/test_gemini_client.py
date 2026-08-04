from app.llm import gemini_client


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("bad response")

    def json(self):
        return self._payload


def test_call_gemini_returns_text(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse({
            "candidates": [
                {"content": {"parts": [{"text": "hello from gemini"}]}}
            ]
        })

    monkeypatch.setattr(gemini_client.requests, "post", fake_post)
    monkeypatch.setattr(gemini_client.settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_client.settings, "GEMINI_MODEL", "gemini-2.0-flash")

    result = gemini_client.call_gemini("ignored-model", "system", "prompt")

    assert result == "hello from gemini"
    assert captured["url"].startswith("https://generativelanguage.googleapis.com")
    assert captured["json"]["systemInstruction"]["parts"][0]["text"] == "system"


def test_is_gemini_up_uses_recent_successful_generation(monkeypatch):
    monkeypatch.setattr(gemini_client.settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_client, "_liveness", {"ts": 0.0, "up": False})

    def fake_post(url, json=None, timeout=None):
        return FakeResponse({
            "candidates": [
                {"content": {"parts": [{"text": "ok"}]}}
            ]
        })

    monkeypatch.setattr(gemini_client.requests, "post", fake_post)

    gemini_client.call_gemini("ignored-model", "system", "prompt")

    assert gemini_client.is_gemini_up() is True
