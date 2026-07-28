"""Audit trail route: read-only view of the append-only activity log."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.db_models import User
from app.repositories import audit_repo
from app.schemas.audit import AuditEventOut, AuditTrail

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditTrail)
def audit_trail(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AuditTrail:
    """Most recent events first. There is no write endpoint by design —
    entries are appended by the actions themselves."""
    return AuditTrail(
        total=audit_repo.total(db),
        counts_by_action=audit_repo.counts_by_action(db),
        events=[AuditEventOut.model_validate(e) for e in audit_repo.recent(db, limit)],
    )
