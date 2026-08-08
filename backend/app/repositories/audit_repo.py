"""
Audit trail data access.

Deliberately offers no update or delete: the only mutation is `record`, which
appends. Recording must never break the request it is attached to, so a
failure here is swallowed and logged rather than raised — an audit write is
observability, not business logic.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database import engine
from app.db_models import AuditEvent

logger = get_logger(__name__)

_MAX_DETAIL = 300


def ensure_table() -> None:
    """Create audit_events if it isn't there yet.

    Existing databases were built before this table existed, so the app
    creates it on startup rather than requiring a re-seed. Only ever creates;
    never drops or alters, so seeded data is untouched.
    """
    AuditEvent.__table__.create(bind=engine, checkfirst=True)


def record(db: Session, *, username: str, action: str, detail: str = "") -> None:
    """Append one event. Never raises."""
    try:
        db.add(
            AuditEvent(
                username=username,
                action=action,
                detail=detail[:_MAX_DETAIL],
            )
        )
        db.commit()
    except Exception:  # pragma: no cover - defensive
        logger.warning("Audit write failed for action=%s", action, exc_info=True)
        db.rollback()


def recent(db: Session, limit: int = 50) -> list[AuditEvent]:
    return list(
        db.execute(
            select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit)
        ).scalars()
    )


def total(db: Session) -> int:
    return db.execute(select(func.count()).select_from(AuditEvent)).scalar_one()


def counts_by_action(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(AuditEvent.action, func.count()).group_by(AuditEvent.action)
    ).all()
    return {action: n for action, n in rows}
