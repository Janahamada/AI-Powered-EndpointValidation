"""
Central, environment-driven configuration.

Every tunable lives here so swapping models, thresholds, secrets, or the
database doesn't require touching business logic. Values can be overridden
via environment variables or a `.env` file (see `.env.example`).
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = two levels up from this file (backend/app/config.py -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "AI-Powered Endpoint Assurance Validation"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # --- CORS ---
    # Comma-separated list of allowed origins for the SPA dev/prod hosts.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Database ---
    # SQLAlchemy connection URL. Defaults to the SQLite file at the repo root.
    #   SQL Server : mssql+pyodbc://user:pass@server/EndpointSecurity?driver=ODBC+Driver+18+for+SQL+Server
    #   PostgreSQL : postgresql+psycopg2://user:pass@localhost/endpoint_security
    DATABASE_URL: str = f"sqlite:///{(REPO_ROOT / 'endpoint_security.db').as_posix()}"

    # --- Auth / JWT ---
    # SECRET_KEY MUST be overridden in production via the environment.
    SECRET_KEY: str = "CHANGE-ME-in-production-use-a-long-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # Seeded default admin (created by scripts/seed_users.py if the table is empty).
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_ADMIN_EMAIL: str = "admin@endpointassurance.local"

    # --- Ollama (local LLM) ---
    # Explicit IPv4 (not "localhost") so a liveness probe fails fast when
    # Ollama isn't running, instead of waiting on an IPv6 ::1 connect timeout.
    OLLAMA_HOST: str = "http://127.0.0.1:11434"
    # EXPLANATION_MODEL  -> chat "why/what" answers (RAG-grounded, quality-first).
    # RECOMMENDATION_MODEL -> RAG-grounded remediation recommendations (the model
    #                         reads retrieved policy/CIS excerpts and writes them).
    EXPLANATION_MODEL: str = "smollm2:1.7b"
    RECOMMENDATION_MODEL: str = "smollm2:1.7b"
    EXTRACTION_MODEL: str = "smollm2:360m"
    OLLAMA_TIMEOUT: int = 120
    # Master switch: when False the AI layer always uses the deterministic
    # fallback, never attempting an Ollama call. When True it tries Ollama and
    # degrades gracefully if it is unreachable.
    AI_ENABLED: bool = True

    # --- Evaluation reference time ---
    # Time-based freshness rules (EDR check-in, AV signature age, ...) are
    # evaluated against this instant. Leave empty to anchor to the dataset's
    # own most-recent evidence timestamp — correct for replaying a static
    # evidence snapshot, and stable as the wall clock advances. Set to an ISO
    # datetime to pin it, or the literal "now" to use the real wall clock
    # (appropriate once live evidence is flowing).
    EVAL_REFERENCE_TIME: str = ""

    # --- RAG ---
    POLICIES_ROOT: str = str(REPO_ROOT / "policies")
    CHROMA_PATH: str = str(REPO_ROOT / "chroma_store")
    RAG_TOP_K: int = 3
    EMBEDDING_MODEL: str = "nomic-embed-text"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def collections(self) -> dict[str, str]:
        # Two isolated Chroma collections, one per policies subfolder, so a
        # query targeting one can never structurally return chunks from the
        # other.
        return {"master_policies": "master_policies", "standards": "standards"}


# Severity ordering shared across the compliance/validation layer.
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so settings are parsed once per process."""
    return Settings()


settings = get_settings()
