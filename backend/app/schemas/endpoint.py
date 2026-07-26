"""Endpoint list/detail contracts returned by the API."""

from typing import Optional

from pydantic import BaseModel

from app.schemas.control import ControlRecord, Finding
from app.schemas.recommendation import Recommendation


class AssetOut(BaseModel):
    hostname: str
    ip_address: str
    operating_system: str
    business_owner: str


class ControlValidation(BaseModel):
    """Result of validating one control against the blueprint."""

    control_type: str
    label: str
    status: str  # ValidationStatus value
    present: bool
    score: float  # 0..100, share of this control's fields that pass
    total_fields: int
    passed_fields: int
    findings: list[Finding] = []


class EndpointSummary(BaseModel):
    """One row in the endpoints table."""

    hostname: str
    ip_address: str
    operating_system: str
    business_owner: str
    status: str  # worst control status
    compliance_score: float  # 0..100 across all controls
    critical_findings: int
    high_findings: int
    total_findings: int
    control_statuses: dict[str, str]  # control_type -> status


class EndpointDetail(BaseModel):
    asset: AssetOut
    status: str
    compliance_score: float
    controls: list[ControlValidation]
    evidence: ControlRecord
    findings: list[Finding]  # all findings, severity-sorted
    recommendations: list[Recommendation] = []  # deterministic, grounded, cited
    ai_summary: Optional[str] = None  # optional LLM narrative on top
    ai_available: bool = False  # whether the LLM narrative layer answered


class PaginatedEndpoints(BaseModel):
    items: list[EndpointSummary]
    total: int
    page: int
    page_size: int
    total_pages: int
