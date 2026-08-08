"""Finding lifecycle contracts."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

FindingStatus = Literal["in_progress", "risk_accepted", "false_positive"]


class FindingStateIn(BaseModel):
    hostname: str
    control_type: str
    field: str
    status: FindingStatus
    justification: str = Field("", max_length=1000)
    owner: str = Field("", max_length=120)
    expires_at: Optional[datetime] = None

    @model_validator(mode="after")
    def require_governance_fields(self):
        """A risk acceptance without a reason and an end date isn't a decision,
        it's a shrug — so both are mandatory for that status."""
        if self.status == "risk_accepted":
            if not self.justification.strip():
                raise ValueError("A risk acceptance requires a justification.")
            if self.expires_at is None:
                raise ValueError("A risk acceptance must have an expiry date.")
        if self.status == "false_positive" and not self.justification.strip():
            raise ValueError("Marking a finding a false positive requires a justification.")
        return self


class FindingStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hostname: str
    control_type: str
    field: str
    status: FindingStatus
    justification: str
    owner: str
    expires_at: Optional[datetime]
    updated_by: str
    updated_at: datetime


class FindingStateView(FindingStateOut):
    """As stored, plus whether a time-boxed acceptance has lapsed."""

    expired: bool = False


class FindingGovernance(BaseModel):
    counts_by_status: dict[str, int]
    expired_acceptances: int
