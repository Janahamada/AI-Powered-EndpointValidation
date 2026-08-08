"""Shared enums and small value types used across the API contracts."""

from enum import Enum


class ControlType(str, Enum):
    ANTIVIRUS = "antivirus"
    EDR = "edr"
    DLP = "dlp"
    BITLOCKER = "bitlocker"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationStatus(str, Enum):
    """Per-control / per-endpoint outcome shown in the UI."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    NO_DATA = "NO_DATA"


# Human-readable labels for each control type.
CONTROL_LABELS: dict[str, str] = {
    ControlType.ANTIVIRUS: "Antivirus",
    ControlType.EDR: "Endpoint Detection & Response",
    ControlType.DLP: "Data Loss Prevention",
    ControlType.BITLOCKER: "BitLocker Encryption",
}
