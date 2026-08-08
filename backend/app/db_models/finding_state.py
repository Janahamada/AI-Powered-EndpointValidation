"""
Finding lifecycle ORM model — the governance layer over the rules engine.

A finding is *detected* deterministically by the compliance engine; this table
records what the organisation decided to DO about it. The two are deliberately
separate: nothing here feeds back into validation or scoring, so a risk
acceptance can never make a failing control look like it passes.

Identity is (hostname, control_type, field) — stable across re-evaluation, so a
decision survives the next collection run and re-attaches to the same finding.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

#: Decisions an analyst can record. Absence of a row means "open".
FINDING_STATUSES = ("in_progress", "risk_accepted", "false_positive")


class FindingState(Base):
    __tablename__ = "finding_states"
    __table_args__ = (
        UniqueConstraint("hostname", "control_type", "field", name="uq_finding_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hostname: Mapped[str] = mapped_column(String, nullable=False, index=True)
    control_type: Mapped[str] = mapped_column(String, nullable=False)
    field: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[str] = mapped_column(String, nullable=False)
    justification: Mapped[str] = mapped_column(String, nullable=False, default="")
    owner: Mapped[str] = mapped_column(String, nullable=False, default="")
    #: Risk acceptances are time-boxed; an expired one is surfaced as open again.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    updated_by: Mapped[str] = mapped_column(String, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
