"""
Blueprint (assurance baseline) rule ORM model.

`expected` is stored as JSON text so bool/int/str values round-trip with
their real type instead of collapsing to strings. `control_type` groups a
rule under one of the four controls for per-control validation & UI grouping.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BlueprintRule(Base):
    __tablename__ = "blueprint_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    control_type: Mapped[str] = mapped_column(String, nullable=False)  # antivirus/edr/firewall/bitlocker
    field: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    operator: Mapped[str] = mapped_column(String, nullable=False)  # eq/lte/gte
    expected: Mapped[str] = mapped_column(String, nullable=False)  # JSON-encoded
    severity: Mapped[str] = mapped_column(String, nullable=False)  # critical/high/medium/low
    description: Mapped[str] = mapped_column(String, nullable=False)
