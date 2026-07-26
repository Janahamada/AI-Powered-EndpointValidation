"""
Shared pytest fixtures.

Tests run against the seeded application database (read-only for API tests).
`client` is a FastAPI TestClient; `auth_headers` performs a real login so the
JWT + dependency chain is exercised end-to-end.
"""

import warnings

import pytest
from fastapi.testclient import TestClient

warnings.filterwarnings("ignore")

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def auth_headers(client: TestClient) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        data={
            "username": settings.DEFAULT_ADMIN_USERNAME,
            "password": settings.DEFAULT_ADMIN_PASSWORD,
        },
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
