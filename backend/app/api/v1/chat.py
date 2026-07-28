"""AI chat route: natural-language questions over the inventory."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.db_models import User
from app.llm.ollama_client import is_ollama_up
from app.repositories import audit_repo
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    # The answer is produced first and passed through untouched; the audit
    # write only observes it.
    response = chat_service.answer(db, payload.message)
    audit_repo.record(
        db,
        username=current_user.username,
        action="chat_query",
        detail=f"[{response.answer_type}] {payload.message}",
    )
    return response


@router.get("/status")
def ai_status(_: User = Depends(get_current_user)) -> dict:
    """Lets the UI show whether the LLM narrative layer is currently online."""
    up = is_ollama_up()
    return {
        "ollama_online": up,
        "message": "AI narrative layer online."
        if up
        else "AI narrative layer offline — deterministic results are still fully available.",
    }
