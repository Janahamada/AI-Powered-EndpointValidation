"""
Data access layer. Schema is defined in sql/schema.sql
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine, text

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL
from models import Asset, ControlRecord

_engine = create_engine(DATABASE_URL)


def _parse_dt(value) -> Optional[datetime]:
    """Timestamps come back as datetime objects from most drivers but as
    strings from SQLite — normalize so age calculations below don't care
    which backend is in use."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _hours_since(dt: Optional[datetime]) -> Optional[int]:
    if dt is None:
        return None
    return int((datetime.now() - dt).total_seconds() // 3600)


def _days_since(dt: Optional[datetime]) -> Optional[int]:
    hours = _hours_since(dt)
    return None if hours is None else hours // 24


def get_asset_by_ip(ip: str) -> Optional[Asset]:
    with _engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM assets WHERE ip_address = :ip"), {"ip": ip}
        ).mappings().fetchone()
        if row is None:
            return None
        return Asset(
            hostname=row["hostname"],
            ip=row["ip_address"],
            operating_system=row["operating_system"],
            business_owner=row["business_owner"],
        )


def get_controls_by_hostname(hostname: str) -> Optional[ControlRecord]:
    """Returns None only if there's no AV *and* no EDR evidence at all for
    this hostname. Partial evidence (one but not the other) is returned
    with the missing side's fields as None — the comparator treats a
    None field as a gap rather than skipping it silently."""
    with _engine.connect() as conn:
        av = conn.execute(
            text("SELECT * FROM av_controls WHERE hostname = :hostname"), {"hostname": hostname}
        ).mappings().fetchone()
        edr = conn.execute(
            text("SELECT * FROM edr_controls WHERE hostname = :hostname"), {"hostname": hostname}
        ).mappings().fetchone()

    if av is None and edr is None:
        return None

    return ControlRecord(
        hostname=hostname,
        av_installed=bool(av["installed"]) if av else False,
        av_version=av["version"] if av else None,
        av_realtime_protection=bool(av["realtime_protection"]) if av else None,
        av_tamper_protection=bool(av["tamper_protection"]) if av else None,
        av_policy=av["policy"] if av else None,
        av_signature_age_days=_days_since(_parse_dt(av["last_update"])) if av else None,
        edr_sensor_installed=bool(edr["sensor_installed"]) if edr else False,
        edr_sensor_version=edr["sensor_version"] if edr else None,
        edr_protection_status=edr["protection_status"] if edr else None,
        edr_isolation_status=edr["isolation_status"] if edr else None,
        edr_policy=edr["policy"] if edr else None,
        edr_last_checkin_hours=_hours_since(_parse_dt(edr["last_checkin"])) if edr else None,
        edr_detection_count=edr["detection_count"] if edr else 0,
    )
