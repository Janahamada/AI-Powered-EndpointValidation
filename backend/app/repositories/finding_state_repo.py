"""
Finding lifecycle data access.

Read/write of analyst decisions only. Nothing in this module is consulted by
the validators, the scoring functions, or the dashboard aggregates — the
compliance verdict stays purely deterministic.
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import engine
from app.db_models import FindingState


def ensure_table() -> None:
    """Create finding_states if absent. Creates only; never drops or alters."""
    FindingState.__table__.create(bind=engine, checkfirst=True)


def get_for_host(db: Session, hostname: str) -> list[FindingState]:
    return list(
        db.execute(
            select(FindingState).where(FindingState.hostname == hostname)
        ).scalars()
    )


def get_one(
    db: Session, hostname: str, control_type: str, field: str
) -> FindingState | None:
    return db.execute(
        select(FindingState).where(
            FindingState.hostname == hostname,
            FindingState.control_type == control_type,
            FindingState.field == field,
        )
    ).scalar_one_or_none()


def upsert(
    db: Session,
    *,
    hostname: str,
    control_type: str,
    field: str,
    status: str,
    justification: str,
    owner: str,
    expires_at: datetime | None,
    updated_by: str,
) -> FindingState:
    row = get_one(db, hostname, control_type, field)
    if row is None:
        row = FindingState(hostname=hostname, control_type=control_type, field=field)
        db.add(row)
    row.status = status
    row.justification = justification
    row.owner = owner
    row.expires_at = expires_at
    row.updated_by = updated_by
    row.updated_at = datetime.now()
    db.commit()
    db.refresh(row)
    return row


def clear(db: Session, hostname: str, control_type: str, field: str) -> bool:
    """Return a finding to 'open'. Returns True if a decision was removed."""
    row = get_one(db, hostname, control_type, field)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def counts_by_status(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(FindingState.status, func.count()).group_by(FindingState.status)
    ).all()
    return {status: n for status, n in rows}


def expired_acceptances(db: Session, now: datetime | None = None) -> list[FindingState]:
    """Risk acceptances whose expiry has passed — these are open again."""
    moment = now or datetime.now()
    return list(
        db.execute(
            select(FindingState).where(
                FindingState.status == "risk_accepted",
                FindingState.expires_at.is_not(None),
                FindingState.expires_at < moment,
            )
        ).scalars()
    )
