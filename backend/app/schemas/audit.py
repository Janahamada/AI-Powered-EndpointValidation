"""Audit trail contracts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: datetime
    username: str
    action: str
    detail: str


class AuditTrail(BaseModel):
    total: int
    counts_by_action: dict[str, int]
    events: list[AuditEventOut]
