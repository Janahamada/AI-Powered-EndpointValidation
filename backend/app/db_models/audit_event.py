"""
Audit event ORM model — the platform's append-only activity trail.

Immutability is by construction, not by database trigger: the repository
exposes only an insert and reads, and no route or service anywhere updates or
deletes a row. `occurred_at` is set by the database, so a caller cannot
backdate an entry.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), index=True
    )
    username: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # login / login_failed / report_generated / chat_query
    action: Mapped[str] = mapped_column(String, nullable=False, index=True)
    detail: Mapped[str] = mapped_column(String, nullable=False, default="")
