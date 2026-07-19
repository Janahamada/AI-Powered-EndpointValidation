"""
Deterministic compliance comparison. Intentionally contains zero LLM calls.

Why: an LLM asked to "compare these fields against this policy" will not
give you the same answer twice on identical input, and won't reliably
catch every gap. A field diff is a solved problem in plain code — use it
for that, and save the LLM for the part it's actually good at
(turning a findings list into readable, policy-grounded prose).
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import ControlRecord, BlueprintRule, Finding, ComplianceResult
from config import SEVERITY_ORDER


def _rule_passes(actual_value, rule: BlueprintRule) -> bool:
    if rule.operator == "eq":
        return actual_value == rule.expected
    if rule.operator == "lte":
        return actual_value <= rule.expected
    if rule.operator == "gte":
        return actual_value >= rule.expected
    raise ValueError(f"Unknown operator: {rule.operator}")


def compare_controls_to_blueprint(
    controls: ControlRecord, blueprint: list[BlueprintRule]
) -> ComplianceResult:
    findings: list[Finding] = []

    for rule in blueprint:
        actual_value = getattr(controls, rule.field, None)
        if actual_value is None:
            # Field missing entirely from the control record — treat as a gap,
            # don't silently skip it.
            findings.append(Finding(
                field=rule.field, expected=rule.expected, actual="missing",
                severity=rule.severity,
                description=f"{rule.description} (field not reported by control)",
            ))
            continue

        if not _rule_passes(actual_value, rule):
            findings.append(Finding(
                field=rule.field, expected=rule.expected, actual=actual_value,
                severity=rule.severity, description=rule.description,
            ))

    findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 99))

    return ComplianceResult(
        hostname=controls.hostname,
        compliant=len(findings) == 0,
        findings=findings,
    )
