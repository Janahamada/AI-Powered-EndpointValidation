"""
Shared data contracts. Every module passes these around instead of raw
dicts, so a bad LLM output or a bad DB row fails loudly at the boundary
instead of silently propagating as a KeyError three modules downstream.
"""

from typing import Literal, Optional
from pydantic import BaseModel, field_validator
import re

IP_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$"
)

Intent = Literal["existence_check", "compliance_check", "unknown"]


class ExtractionResult(BaseModel):
    """Output of LLM call 1. Validated before anything downstream trusts it."""
    ip: Optional[str] = None
    intent: Intent = "unknown"
    confidence: Literal["high", "low"] = "low"

    @field_validator("ip")
    @classmethod
    def validate_ip_format(cls, v):
        if v is None:
            return v
        if not IP_PATTERN.match(v):
            # Never let a malformed/hallucinated IP reach the database layer.
            return None
        return v


class Asset(BaseModel):
    hostname: str
    ip: str
    operating_system: str
    business_owner: str


class ControlRecord(BaseModel):
    """Combined AV + EDR fields for one hostname, with time-based fields
    already converted to ages (days/hours) relative to now — computed once
    at query time in db/database.py so the comparator never has to know
    about wall-clock time."""
    hostname: str

    av_installed: bool
    av_realtime_protection: Optional[bool] = None
    av_tamper_protection: Optional[bool] = None
    av_signature_age_days: Optional[int] = None  # None if AV not installed / no data

    edr_sensor_installed: bool
    edr_protection_status: Optional[str] = None  # "Healthy" | "Unhealthy"
    edr_isolation_status: Optional[str] = None
    edr_last_checkin_hours: Optional[int] = None
    edr_detection_count: int = 0


class BlueprintRule(BaseModel):
    field: str
    operator: Literal["eq", "lte", "gte"]
    expected: object
    severity: Literal["critical", "high", "medium", "low"]
    description: str


class Finding(BaseModel):
    field: str
    expected: object
    actual: object
    severity: str
    description: str


class ComplianceResult(BaseModel):
    hostname: str
    compliant: bool
    findings: list[Finding] = []
