"""System / assurance-agent routes: evidence collection status & component health."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.db_models import User
from app.llm.gemini_client import is_gemini_enabled, is_gemini_up
from app.services import collection_service

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/collection")
def collection(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """Evidence-collection status for the AI Assurance Agent surface."""
    return collection_service.collection_status(db)


@router.get("/components")
def components(_: User = Depends(get_current_user)) -> dict:
    """High-level status of each named platform component."""
    ai_online = is_gemini_up() or is_gemini_enabled()
    return {
        "components": [
            {"name": "AI Assurance Agent", "role": "Automation & evidence collection", "status": "operational"},
            {"name": "Compliance Engine", "role": "Validation & risk classification", "status": "operational"},
            {"name": "AI Analysis Module", "role": "Insights & recommendations",
             "status": "operational", "detail": "Gemini API enabled" if ai_online else "Deterministic mode (Gemini disabled)"},
            {"name": "Reporting", "role": "PDF & Excel report generation", "status": "operational"},
        ],
        "ai_online": ai_online,
    }
