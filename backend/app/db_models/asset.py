"""Asset inventory ORM model. `hostname` is the natural key everywhere."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    hostname: Mapped[str] = mapped_column(String, primary_key=True)
    ip_address: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    operating_system: Mapped[str] = mapped_column(String, nullable=False)
    business_owner: Mapped[str] = mapped_column(String, nullable=False)
    loaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
