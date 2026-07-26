"""
Control-evidence data access.

Assembles the unified `ControlRecord` for a hostname from all four control
tables, normalizing timestamps to ages at this boundary. A control with no
row at all is reported via its `*_installed`/`*_present` flag = False and its
fields = None, so the validator treats it as a gap rather than skipping it.
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db_models import AvControl, BitlockerControl, DlpControl, EdrControl
from app.repositories.time_utils import days_since, hours_since, parse_dt
from app.schemas.control import ControlRecord


def reference_time(db: Session) -> datetime:
    """The instant against which time-based freshness is measured.

    Priority: an explicit `EVAL_REFERENCE_TIME` setting ("now" = wall clock,
    or an ISO datetime), else the most recent evidence timestamp in the DB
    (so a static snapshot is judged as of its own collection time and doesn't
    rot as the wall clock advances), else wall-clock now as a final fallback.
    """
    configured = settings.EVAL_REFERENCE_TIME.strip()
    if configured:
        if configured.lower() == "now":
            return datetime.now()
        parsed = parse_dt(configured)
        if parsed:
            return parsed

    candidates = [
        db.execute(func.max(EdrControl.last_checkin)).scalar(),
        db.execute(func.max(AvControl.last_update)).scalar(),
        db.execute(func.max(AvControl.last_heartbeat)).scalar(),
    ]
    stamps = [dt for c in candidates if (dt := parse_dt(c)) is not None]
    return max(stamps) if stamps else datetime.now()


def _av(db: Session, hostname: str) -> AvControl | None:
    return db.get(AvControl, hostname)


def _edr(db: Session, hostname: str) -> EdrControl | None:
    return db.get(EdrControl, hostname)


def _dlp(db: Session, hostname: str) -> DlpControl | None:
    return db.get(DlpControl, hostname)


def _bl(db: Session, hostname: str) -> BitlockerControl | None:
    return db.get(BitlockerControl, hostname)


def get_control_record(db: Session, hostname: str) -> ControlRecord:
    """Always returns a ControlRecord (never None): absent controls are
    represented as not-present with None fields."""
    ref = reference_time(db)
    return _build_record(
        hostname, _av(db, hostname), _edr(db, hostname), _dlp(db, hostname), _bl(db, hostname), ref
    )


def _build_record(hostname, av, edr, dlp, bl, ref: datetime | None = None) -> ControlRecord:
    return ControlRecord(
        hostname=hostname,
        av_present=av is not None,
        av_installed=bool(av.installed) if av else False,
        av_version=av.version if av else None,
        av_engine_version=av.engine_version if av else None,
        av_signature_version=av.signature_version if av else None,
        av_realtime_protection=bool(av.realtime_protection) if av else None,
        av_tamper_protection=bool(av.tamper_protection) if av else None,
        av_policy=av.policy if av else None,
        av_signature_age_days=days_since(parse_dt(av.last_update), ref) if av else None,
        av_last_heartbeat_hours=hours_since(parse_dt(av.last_heartbeat), ref) if av else None,
        edr_present=edr is not None,
        edr_sensor_installed=bool(edr.sensor_installed) if edr else False,
        edr_sensor_version=edr.sensor_version if edr else None,
        edr_protection_status=edr.protection_status if edr else None,
        edr_isolation_status=edr.isolation_status if edr else None,
        edr_policy=edr.policy if edr else None,
        edr_last_checkin_hours=hours_since(parse_dt(edr.last_checkin), ref) if edr else None,
        edr_detection_count=edr.detection_count if edr else 0,
        dlp_present=dlp is not None,
        dlp_agent_status=dlp.agent_status if dlp else None,
        dlp_data_classification=dlp.data_classification if dlp else None,
        dlp_channel=dlp.channel if dlp else None,
        dlp_action_taken=dlp.action_taken if dlp else None,
        bl_present=bl is not None,
        bl_encryption_method=bl.encryption_method if bl else None,
        bl_protection_status=bl.protection_status if bl else None,
        bl_percentage_encrypted=bl.percentage_encrypted if bl else None,
        bl_volume_status=bl.volume_status if bl else None,
        bl_is_encrypted=bool(bl.is_encrypted)
        if bl and bl.is_encrypted is not None
        else None,
        bl_compliance_state=bl.compliance_state if bl else None,
    )


def get_all_control_records(db: Session) -> dict[str, ControlRecord]:
    """Batch-load every control table once and merge into per-hostname records.
    Used by fleet-wide views to avoid an N+1 query storm."""
    from app.db_models import Asset  # local import avoids a cycle at module load

    av = {r.hostname: r for r in db.execute(select(AvControl)).scalars().all()}
    edr = {r.hostname: r for r in db.execute(select(EdrControl)).scalars().all()}
    dlp = {r.hostname: r for r in db.execute(select(DlpControl)).scalars().all()}
    bl = {r.hostname: r for r in db.execute(select(BitlockerControl)).scalars().all()}
    asset_hosts = set(db.execute(select(Asset.hostname)).scalars().all())
    ref = reference_time(db)

    hosts = asset_hosts | av.keys() | edr.keys() | dlp.keys() | bl.keys()
    return {
        h: _build_record(h, av.get(h), edr.get(h), dlp.get(h), bl.get(h), ref)
        for h in sorted(hosts)
    }


def all_hostnames(db: Session) -> list[str]:
    """Union of every hostname that appears in inventory or any evidence table —
    used by the fleet-wide dashboard aggregation."""
    from app.db_models import Asset  # local import avoids a cycle at module load

    hosts: set[str] = set()
    for model, col in (
        (Asset, Asset.hostname),
        (AvControl, AvControl.hostname),
        (EdrControl, EdrControl.hostname),
        (DlpControl, DlpControl.hostname),
        (BitlockerControl, BitlockerControl.hostname),
    ):
        hosts.update(db.execute(select(col)).scalars().all())
    return sorted(hosts)
