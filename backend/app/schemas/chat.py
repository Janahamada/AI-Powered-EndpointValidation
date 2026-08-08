"""AI chat contracts."""

from typing import Any, Optional

from pydantic import BaseModel

from app.schemas.control import Finding


class ChatRequest(BaseModel):
    message: str


class ChatSource(BaseModel):
    """A reference showing WHERE an answer was derived from."""

    kind: str  # engine | database | blueprint | policy | standard | inventory
    label: str  # human-readable citation


class ChatTableRow(BaseModel):
    """A row in a tabular chat answer (e.g. a list of endpoints)."""

    hostname: Optional[str] = None
    values: dict[str, Any] = {}


class ChatResponse(BaseModel):
    status: str  # ok / clarification_needed / not_found / no_controls_data / error
    answer_type: str = "general"  # endpoint / fleet_metric / list / policy / explanation / clarification
    message: str  # natural-language answer (deterministic template or grounded LLM prose)
    use_case: Optional[str] = None  # existence_check / compliance_check
    hostname: Optional[str] = None
    ip: Optional[str] = None
    compliant: Optional[bool] = None
    findings: list[Finding] = []  # what is wrong (deterministic)
    ai_recommendations: Optional[str] = None  # RAG-generated remediation (how to fix)
    table: list[ChatTableRow] = []  # for list-style answers
    sources: list[ChatSource] = []  # HOW the answer was derived (always populated)
    ai_available: bool = False  # True only when the AI recommendation layer answered
    data: Optional[dict[str, Any]] = None
