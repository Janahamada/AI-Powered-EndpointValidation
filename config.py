"""
Central configuration. Keep every tunable in one place so swapping models
or thresholds doesn't require touching business logic.
"""

# --- Ollama ---
OLLAMA_HOST = "http://localhost:11434"

EXTRACTION_MODEL = "smollm2:135m"
RECOMMENDATION_MODEL = "smollm2:1.7b"

# --- Database ---
# SQLAlchemy connection URL. Examples:
#   SQL Server : "mssql+pyodbc://user:pass@myserver/EndpointSecurity?driver=ODBC+Driver+18+for+SQL+Server"
#   PostgreSQL : "postgresql+psycopg2://user:pass@localhost/endpoint_security"
#   Local dev  : "sqlite:///endpoint_security.db"
DATABASE_URL = "sqlite:///endpoint_security.db"

# --- RAG ---
CHROMA_PATH = "chroma_store"
CHROMA_COLLECTION = "security_policies"
RAG_TOP_K = 3
# Local embedding model served by Ollama — keeps RAG fully offline instead
# of relying on Chroma's default embedding function, which downloads a
# model from the internet on first use.
EMBEDDING_MODEL = "nomic-embed-text"

# --- Compliance ---
# Severity ordering, used for sorting findings before they go to the LLM
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
