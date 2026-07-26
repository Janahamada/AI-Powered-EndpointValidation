"""
Active validator registry.

Order here is the canonical display order across the app (endpoint detail,
dashboard per-control stats). Register a new control's validator here and it
is automatically picked up everywhere — the validation service, endpoint
detail, and dashboard aggregation all iterate this list.
"""

from app.validators.base import ControlValidator
from app.validators.controls import (
    AntivirusValidator,
    BitlockerValidator,
    EdrValidator,
    FirewallValidator,
)

VALIDATORS: list[ControlValidator] = [
    AntivirusValidator(),
    EdrValidator(),
    FirewallValidator(),
    BitlockerValidator(),
]
