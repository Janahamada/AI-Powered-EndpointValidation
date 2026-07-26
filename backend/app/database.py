"""
SQLAlchemy engine + session management.

One engine per process. `get_db` is the FastAPI dependency that yields a
scoped session and always closes it, even on error.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# SQLite needs check_same_thread=False to be used across FastAPI's threadpool.
_connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a session, guarantees cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
