"""
Compliance blueprint, expressed against the real AV/EDR evidence fields.
Edit this list when your standard changes — no code changes needed
elsewhere.
"""

from models import BlueprintRule

BLUEPRINT: list[BlueprintRule] = [
    BlueprintRule(
        field="av_installed", operator="eq", expected=True,
        severity="critical", description="Antivirus must be installed."
    ),
    BlueprintRule(
        field="av_realtime_protection", operator="eq", expected=True,
        severity="critical", description="AV real-time protection must be enabled."
    ),
    BlueprintRule(
        field="av_tamper_protection", operator="eq", expected=True,
        severity="high", description="AV tamper protection must be enabled."
    ),
    BlueprintRule(
        field="av_signature_age_days", operator="lte", expected=7,
        severity="high", description="AV signatures must be updated within 7 days."
    ),
    BlueprintRule(
        field="edr_sensor_installed", operator="eq", expected=True,
        severity="critical", description="EDR sensor must be installed."
    ),
    BlueprintRule(
        field="edr_protection_status", operator="eq", expected="Healthy",
        severity="critical", description="EDR sensor must report a healthy protection status."
    ),
    BlueprintRule(
        field="edr_last_checkin_hours", operator="lte", expected=24,
        severity="medium", description="EDR agent must check in at least every 24 hours."
    ),
]


def get_blueprint() -> list[BlueprintRule]:
    return BLUEPRINT
