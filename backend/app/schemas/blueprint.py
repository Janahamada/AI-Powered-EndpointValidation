"""Contracts for the Blueprint / Policies view — 'what we validate against'."""

from typing import Any, Optional

from pydantic import BaseModel

from app.schemas.recommendation import CisReference


class BlueprintRuleView(BaseModel):
    field: str
    operator: str  # eq / lte / gte
    operator_label: str  # "must equal" / "must be at least" / "must be at most"
    expected: Any
    severity: str
    description: str
    cis: Optional[CisReference] = None  # supporting standard mapping
    policy_reference: str  # our control policy / golden-image baseline


class ControlBlueprint(BaseModel):
    control_type: str
    label: str
    rule_count: int
    golden_image: Optional[dict[str, Any]] = None  # reference config for fw/bl
    rules: list[BlueprintRuleView]


class PolicyDoc(BaseModel):
    id: str  # e.g. "AV-01"
    title: str
    text: str


class BlueprintView(BaseModel):
    total_rules: int
    controls: list[ControlBlueprint]
    policies: list[PolicyDoc]  # internal AV/EDR control policies
    standard_name: str
    standard_controls: int
    standard_safeguards: int
