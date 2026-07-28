"""
Finding lifecycle routes.

Records what was decided about a finding — in progress, risk accepted (with a
justification and an expiry), or disputed as a false positive. Detection stays
with the compliance engine; these routes never touch it, so scores and statuses
are unaffected by any decision recorded here.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.db_models import User
from app.repositories import audit_repo, finding_state_repo
from app.schemas.finding_state import (
    FindingGovernance,
    FindingStateIn,
    FindingStateView,
)

router = APIRouter(prefix="/findings", tags=["findings"])


def _to_view(row) -> FindingStateView:
    expired = bool(
        row.status == "risk_accepted"
        and row.expires_at is not None
        and row.expires_at < datetime.now()
    )
    return FindingStateView(
        hostname=row.hostname,
        control_type=row.control_type,
        field=row.field,
        status=row.status,
        justification=row.justification,
        owner=row.owner,
        expires_at=row.expires_at,
        updated_by=row.updated_by,
        updated_at=row.updated_at,
        expired=expired,
    )


@router.get("/states", response_model=list[FindingStateView])
def states_for_host(
    hostname: str = Query(..., description="Endpoint hostname"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[FindingStateView]:
    return [_to_view(r) for r in finding_state_repo.get_for_host(db, hostname)]


@router.put("/state", response_model=FindingStateView)
def set_state(
    payload: FindingStateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FindingStateView:
    row = finding_state_repo.upsert(
        db,
        hostname=payload.hostname,
        control_type=payload.control_type,
        field=payload.field,
        status=payload.status,
        justification=payload.justification.strip(),
        owner=payload.owner.strip(),
        expires_at=payload.expires_at,
        updated_by=current_user.username,
    )
    audit_repo.record(
        db,
        username=current_user.username,
        action="finding_state_changed",
        detail=(
            f"{payload.hostname} · {payload.control_type}.{payload.field} "
            f"-> {payload.status}"
            + (f" (until {payload.expires_at:%Y-%m-%d})" if payload.expires_at else "")
        ),
    )
    return _to_view(row)


@router.delete("/state")
def clear_state(
    hostname: str,
    control_type: str,
    field: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    removed = finding_state_repo.clear(db, hostname, control_type, field)
    if removed:
        audit_repo.record(
            db,
            username=current_user.username,
            action="finding_state_changed",
            detail=f"{hostname} · {control_type}.{field} -> open (recommendation withdrawn)",
        )
    return {"cleared": removed}


@router.get("/governance", response_model=FindingGovernance)
def governance(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FindingGovernance:
    return FindingGovernance(
        counts_by_status=finding_state_repo.counts_by_status(db),
        expired_acceptances=len(finding_state_repo.expired_acceptances(db)),
    )
