"""AI chat route: natural-language questions over the inventory."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.db_models import User
from app.llm.ollama_client import is_ollama_up
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ChatResponse:
    return chat_service.answer(db, payload.message)


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
