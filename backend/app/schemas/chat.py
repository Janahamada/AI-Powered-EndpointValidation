"""AI chat contracts."""

from typing import Any, Optional

from pydantic import BaseModel

from app.schemas.control import Finding
from app.schemas.recommendation import Recommendation


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
    findings: list[Finding] = []
    recommendations: list[Recommendation] = []  # structured, grounded, cited
    table: list[ChatTableRow] = []  # for list-style answers
    sources: list[ChatSource] = []  # HOW the answer was derived (always populated)
    ai_summary: Optional[str] = None  # optional LLM narrative
    ai_available: bool = False  # True only when the LLM narrative answered
    data: Optional[dict[str, Any]] = None
