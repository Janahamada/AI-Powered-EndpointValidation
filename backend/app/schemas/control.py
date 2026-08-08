"""
Control-evidence and finding contracts.

`ControlRecord` is the unified, time-normalized view of all four controls
for one hostname — time fields are already converted to ages (days/hours)
at the repository boundary so the validators never touch wall-clock time.
This is the single object every validator reads via `getattr`.
"""

import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, field_validator

IP_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$"
)

Intent = Literal["existence_check", "compliance_check", "unknown"]


class ExtractionResult(BaseModel):
    """Output of the LLM intent/entity extraction. Validated before anything
    downstream trusts it — a malformed/hallucinated IP becomes None here."""

    ip: Optional[str] = None
    intent: Intent = "unknown"
    confidence: Literal["high", "low"] = "low"

    @field_validator("ip")
    @classmethod
    def validate_ip_format(cls, v):
        if v is None:
            return v
        return v if IP_PATTERN.match(v) else None

    @field_validator("intent", mode="before")
    @classmethod
    def coerce_intent(cls, v):
        if v not in ("existence_check", "compliance_check", "unknown"):
            return "unknown"
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v):
        return v if v in ("high", "low") else "low"


class ControlRecord(BaseModel):
    """Combined AV + EDR + Firewall + BitLocker fields for one hostname."""

    hostname: str

    # --- Antivirus ---
    av_present: bool = False  # an AV evidence row exists for this host
    av_installed: bool = False
    av_version: Optional[str] = None
    av_engine_version: Optional[str] = None
    av_signature_version: Optional[str] = None
    av_realtime_protection: Optional[bool] = None
    av_tamper_protection: Optional[bool] = None
    av_policy: Optional[str] = None
    av_signature_age_days: Optional[int] = None
    av_last_heartbeat_hours: Optional[int] = None

    # --- EDR ---
    edr_present: bool = False  # an EDR evidence row exists for this host
    edr_sensor_installed: bool = False
    edr_sensor_version: Optional[str] = None
    edr_protection_status: Optional[str] = None  # "Healthy" | "Unhealthy"
    edr_isolation_status: Optional[str] = None
    edr_policy: Optional[str] = None
    edr_last_checkin_hours: Optional[int] = None
    edr_detection_count: int = 0

    # --- DLP ---
    dlp_present: bool = False
    dlp_agent_status: Optional[str] = None
    dlp_data_classification: Optional[str] = None
    dlp_channel: Optional[str] = None
    dlp_action_taken: Optional[str] = None

    # --- BitLocker ---
    bl_present: bool = False
    bl_encryption_method: Optional[str] = None
    bl_protection_status: Optional[str] = None
    bl_percentage_encrypted: Optional[int] = None
    bl_volume_status: Optional[str] = None
    bl_is_encrypted: Optional[bool] = None
    bl_compliance_state: Optional[str] = None


class Finding(BaseModel):
    """One deterministic gap between actual evidence and the blueprint."""

    control_type: str
    field: str
    expected: Any
    actual: Any
    severity: str
    description: str


class BlueprintRuleOut(BaseModel):
    control_type: str
    field: str
    operator: Literal["eq", "lte", "gte"]
    expected: Any
    severity: str
    description: str
