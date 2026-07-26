"""
Validation service: runs every registered control validator over one
endpoint's evidence and rolls the per-control results up into an endpoint
status + compliance score.

Status roll-up (worst wins): FAIL > NO_DATA > WARNING > PASS.
Compliance score: total passing fields / total evaluated fields across all
four controls (a missing control contributes 0/​N, correctly dragging the
score down).
"""

from app.config import SEVERITY_ORDER
from app.schemas.common import ValidationStatus
from app.schemas.control import BlueprintRuleOut, ControlRecord, Finding
from app.schemas.endpoint import ControlValidation
from app.validators.registry import VALIDATORS

# Worst-first ordering for rolling control statuses up to the endpoint.
_STATUS_RANK = {
    ValidationStatus.FAIL.value: 0,
    ValidationStatus.NO_DATA.value: 1,
    ValidationStatus.WARNING.value: 2,
    ValidationStatus.PASS.value: 3,
}


def validate_controls(
    record: ControlRecord, rules: list[BlueprintRuleOut]
) -> list[ControlValidation]:
    """Per-control validation, in canonical registry order."""
    return [v.evaluate(record, rules) for v in VALIDATORS]


def endpoint_status(controls: list[ControlValidation]) -> str:
    if not controls:
        return ValidationStatus.NO_DATA.value
    return min(controls, key=lambda c: _STATUS_RANK.get(c.status, 99)).status


def compliance_score(controls: list[ControlValidation]) -> float:
    total = sum(c.total_fields for c in controls)
    passed = sum(c.passed_fields for c in controls)
    if total == 0:
        return 0.0
    return round(passed / total * 100.0, 1)


def all_findings(controls: list[ControlValidation]) -> list[Finding]:
    findings = [f for c in controls for f in c.findings]
    findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 99))
    return findings
