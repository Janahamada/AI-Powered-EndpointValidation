"""Report routes: fleet PDF, per-endpoint PDF, findings Excel workbook."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.db_models import User
from app.repositories import audit_repo
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])

_PDF = "application/pdf"
_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _attachment(filename: str) -> dict[str, str]:
    return {"Content-Disposition": f'attachment; filename="{filename}"'}


@router.get("/fleet.pdf")
def fleet_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    data = report_service.fleet_report_pdf(db)
    audit_repo.record(
        db,
        username=current_user.username,
        action="report_generated",
        detail="Fleet assurance report (PDF).",
    )
    return Response(content=data, media_type=_PDF, headers=_attachment("fleet_assurance_report.pdf"))


@router.get("/findings.xlsx")
def findings_xlsx(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    data = report_service.findings_workbook(db)
    audit_repo.record(
        db,
        username=current_user.username,
        action="report_generated",
        detail="Findings export (Excel).",
    )
    return Response(content=data, media_type=_XLSX, headers=_attachment("findings_export.xlsx"))


@router.get("/endpoint/{hostname}.pdf")
def endpoint_pdf(
    hostname: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    data = report_service.endpoint_report_pdf(db, hostname)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No endpoint '{hostname}' found.",
        )
    audit_repo.record(
        db,
        username=current_user.username,
        action="report_generated",
        detail=f"Endpoint report (PDF) — {hostname}.",
    )
    return Response(
        content=data, media_type=_PDF,
        headers=_attachment(f"endpoint_report_{hostname}.pdf"),
    )
