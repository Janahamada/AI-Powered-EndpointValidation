"""
Control validator base class.

Each validator evaluates ONE control (Antivirus, EDR, DLP, BitLocker)
for one endpoint against the blueprint rules that belong to that control, and
returns a `ControlValidation` with a PASS/WARNING/FAIL/NO_DATA status, a
0..100 score, and the list of findings.

The field-diff itself is deterministic and identical across controls, so it
lives here (DRY). Subclasses only declare metadata: which control they are,
their label, and the record field that signals the control's presence. This
keeps adding a fifth control to "subclass + register", nothing more (OCP).
"""

from abc import ABC

from app.config import SEVERITY_ORDER
from app.schemas.common import CONTROL_LABELS, ControlType, ValidationStatus
from app.schemas.control import BlueprintRuleOut, ControlRecord, Finding
from app.schemas.endpoint import ControlValidation


def rule_passes(actual_value, rule: BlueprintRuleOut) -> bool:
    """Deterministic comparison. Shared by every control."""
    op = rule.operator
    if op == "eq":
        return actual_value == rule.expected
    if op == "lte":
        return actual_value <= rule.expected
    if op == "gte":
        return actual_value >= rule.expected
    raise ValueError(f"Unknown operator: {op}")


def _status_from_findings(findings: list[Finding]) -> ValidationStatus:
    """Any critical/high finding fails the control; medium/low warns; none passes."""
    if not findings:
        return ValidationStatus.PASS
    worst = min(SEVERITY_ORDER.get(f.severity, 99) for f in findings)
    if worst <= SEVERITY_ORDER["high"]:  # critical(0) or high(1)
        return ValidationStatus.FAIL
    return ValidationStatus.WARNING


class ControlValidator(ABC):
    control_type: ControlType
    presence_field: str  # ControlRecord attribute that is truthy when present

    @property
    def label(self) -> str:
        return CONTROL_LABELS[self.control_type]

    def is_present(self, record: ControlRecord) -> bool:
        return bool(getattr(record, self.presence_field, False))

    def evaluate(
        self, record: ControlRecord, rules: list[BlueprintRuleOut]
    ) -> ControlValidation:
        my_rules = [r for r in rules if r.control_type == self.control_type.value]
        total = len(my_rules)

        # --- No evidence row at all: cannot assess -> NO_DATA. ---
        # (A control that reports "installed = false" DOES have a row and is
        #  handled by the field diff below via the blueprint's install rule,
        #  which fires it as a critical FAIL.)
        if not self.is_present(record):
            finding = Finding(
                control_type=self.control_type.value,
                field=self.presence_field,
                expected=True,
                actual=False,
                severity="high",
                description=f"No {self.label} evidence is on file for this endpoint; "
                f"the control could not be assessed.",
            )
            return ControlValidation(
                control_type=self.control_type.value,
                label=self.label,
                status=ValidationStatus.NO_DATA.value,
                present=False,
                score=0.0,
                total_fields=max(total, 1),
                passed_fields=0,
                findings=[finding],
            )

        # --- Control present: run the deterministic field diff. ---
        findings: list[Finding] = []
        passed = 0
        for rule in my_rules:
            actual = getattr(record, rule.field, None)
            if actual is None:
                findings.append(
                    Finding(
                        control_type=self.control_type.value,
                        field=rule.field,
                        expected=rule.expected,
                        actual="missing",
                        severity=rule.severity,
                        description=f"{rule.description} (field not reported by control)",
                    )
                )
                continue
            if rule_passes(actual, rule):
                passed += 1
            else:
                findings.append(
                    Finding(
                        control_type=self.control_type.value,
                        field=rule.field,
                        expected=rule.expected,
                        actual=actual,
                        severity=rule.severity,
                        description=rule.description,
                    )
                )

        findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 99))
        score = (passed / total * 100.0) if total else 100.0
        return ControlValidation(
            control_type=self.control_type.value,
            label=self.label,
            status=_status_from_findings(findings).value,
            present=True,
            score=round(score, 1),
            total_fields=total,
            passed_fields=passed,
            findings=findings,
        )
