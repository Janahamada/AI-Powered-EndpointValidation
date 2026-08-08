"""
Assurance-agent / collection service.

Represents the "automation & collection" layer: it reports what evidence the
platform has ingested, how fresh it is, its coverage across the inventory, and
any drift between inventory and evidence. This is the observability surface for
the AI Assurance Agent that automates evidence collection (via the ETL).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db_models import (
    Asset,
    AvControl,
    BitlockerControl,
    BlueprintRule,
    DlpControl,
    EdrControl,
)
from app.repositories.time_utils import parse_dt


def _count(db: Session, model) -> int:
    return db.execute(select(func.count()).select_from(model)).scalar_one()


def collection_status(db: Session) -> dict:
    asset_hosts = set(db.execute(select(Asset.hostname)).scalars().all())
    av_hosts = set(db.execute(select(AvControl.hostname)).scalars().all())
    edr_hosts = set(db.execute(select(EdrControl.hostname)).scalars().all())
    dlp_hosts = set(db.execute(select(DlpControl.hostname)).scalars().all())
    bl_hosts = set(db.execute(select(BitlockerControl.hostname)).scalars().all())
    n_assets = len(asset_hosts) or 1

    def coverage(hosts: set[str]) -> float:
        return round(len(hosts & asset_hosts) / n_assets * 100.0, 1)

    # Freshness = most recent load timestamp across all evidence tables.
    stamps = []
    for model in (AvControl, EdrControl, DlpControl, BitlockerControl, Asset):
        v = db.execute(select(func.max(model.loaded_at))).scalar()
        dt = parse_dt(v)
        if dt:
            stamps.append(dt)
    last_collected = max(stamps).isoformat(sep=" ") if stamps else None

    evidence_without_inventory = sorted(
        (av_hosts | edr_hosts | dlp_hosts | bl_hosts) - asset_hosts
    )
    drift = {
        "evidence_without_inventory": evidence_without_inventory,
        "inventory_without_antivirus": len(asset_hosts - av_hosts),
        "inventory_without_edr": len(asset_hosts - edr_hosts),
        "inventory_without_dlp": len(asset_hosts - dlp_hosts),
        "inventory_without_bitlocker": len(asset_hosts - bl_hosts),
    }

    return {
        "last_collected": last_collected,
        "sources": [
            {"name": "Asset Inventory", "source": "asset_inventory.xlsx", "records": len(asset_hosts)},
            {"name": "Antivirus Evidence", "source": "antivirus_evidence.xlsx",
             "records": len(av_hosts), "coverage": coverage(av_hosts)},
            {"name": "EDR Evidence", "source": "edr_evidence.xlsx",
             "records": len(edr_hosts), "coverage": coverage(edr_hosts)},
            {"name": "DLP Telemetry", "source": "dlp_telemetry.csv",
             "records": len(dlp_hosts), "coverage": coverage(dlp_hosts)},
            {"name": "BitLocker Telemetry", "source": "bitlocker_telemetry.csv",
             "records": len(bl_hosts), "coverage": coverage(bl_hosts)},
        ],
        "blueprint_rules": _count(db, BlueprintRule),
        "drift": drift,
        "total_endpoints": len(asset_hosts),
    }
