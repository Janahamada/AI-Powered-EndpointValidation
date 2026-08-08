"""Dashboard KPI/aggregate contracts."""

from pydantic import BaseModel

from app.schemas.control import Finding


class ControlComplianceStat(BaseModel):
    control_type: str
    label: str
    compliance_rate: float  # 0..100 — share of endpoints PASSing this control
    pass_count: int
    warning_count: int
    fail_count: int
    no_data_count: int


class TrendPoint(BaseModel):
    label: str
    score: float


class DashboardSummary(BaseModel):
    total_endpoints: int
    overall_compliance_score: float  # 0..100
    endpoint_status_breakdown: dict[str, int]  # PASS/WARNING/FAIL/NO_DATA -> count
    findings_by_severity: dict[str, int]  # critical/high/medium/low -> count
    critical_findings: int
    high_risk_findings: int
    per_control: list[ControlComplianceStat]
    top_findings: list[Finding]  # most severe fleet-wide
    trend: list[TrendPoint]
