"""
Control-evidence ORM models: Antivirus, EDR, Firewall, BitLocker.

There is intentionally NO foreign key from these tables to `assets`:
evidence for a hostname not yet in the inventory is a real finding (drift),
not an import error.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AvControl(Base):
    __tablename__ = "av_controls"

    hostname: Mapped[str] = mapped_column(String, primary_key=True)
    installed: Mapped[int] = mapped_column(Integer, nullable=False)  # 0/1
    version: Mapped[str | None] = mapped_column(String)
    engine_version: Mapped[str | None] = mapped_column(String)
    signature_version: Mapped[str | None] = mapped_column(String)
    last_update: Mapped[str | None] = mapped_column(String)  # ISO datetime str
    realtime_protection: Mapped[int] = mapped_column(Integer, nullable=False)
    tamper_protection: Mapped[int] = mapped_column(Integer, nullable=False)
    policy: Mapped[str | None] = mapped_column(String)
    last_heartbeat: Mapped[str | None] = mapped_column(String)
    loaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )


class EdrControl(Base):
    __tablename__ = "edr_controls"

    hostname: Mapped[str] = mapped_column(String, primary_key=True)
    sensor_installed: Mapped[int] = mapped_column(Integer, nullable=False)
    sensor_version: Mapped[str | None] = mapped_column(String)
    last_checkin: Mapped[str | None] = mapped_column(String)
    protection_status: Mapped[str] = mapped_column(String, nullable=False)
    isolation_status: Mapped[str] = mapped_column(String, nullable=False)
    policy: Mapped[str | None] = mapped_column(String)
    detection_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    loaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )


class FirewallControl(Base):
    __tablename__ = "firewall_controls"

    hostname: Mapped[str] = mapped_column(String, primary_key=True)
    domain_profile: Mapped[str | None] = mapped_column(String)  # Enabled/Disabled
    private_profile: Mapped[str | None] = mapped_column(String)
    public_profile: Mapped[str | None] = mapped_column(String)
    default_inbound_action: Mapped[str | None] = mapped_column(String)  # Block/Allow
    loaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )


class BitlockerControl(Base):
    __tablename__ = "bitlocker_controls"

    hostname: Mapped[str] = mapped_column(String, primary_key=True)
    encryption_method: Mapped[str | None] = mapped_column(String)  # XtsAes256 / None
    protection_status: Mapped[str | None] = mapped_column(String)  # On/Off
    percentage_encrypted: Mapped[int | None] = mapped_column(Integer)
    volume_status: Mapped[str | None] = mapped_column(String)  # FullyEncrypted/...
    is_encrypted: Mapped[int | None] = mapped_column(Integer)  # 0/1
    compliance_state: Mapped[str | None] = mapped_column(String)
    loaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
