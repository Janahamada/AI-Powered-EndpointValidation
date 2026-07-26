"""Asset inventory data access."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import Asset
from app.schemas.endpoint import AssetOut


def _to_out(row: Asset) -> AssetOut:
    return AssetOut(
        hostname=row.hostname,
        ip_address=row.ip_address,
        operating_system=row.operating_system,
        business_owner=row.business_owner,
    )


def list_all(db: Session) -> list[AssetOut]:
    rows = db.execute(select(Asset).order_by(Asset.hostname)).scalars().all()
    return [_to_out(r) for r in rows]


def get_by_hostname(db: Session, hostname: str) -> AssetOut | None:
    row = db.get(Asset, hostname)
    return _to_out(row) if row else None


def get_by_ip(db: Session, ip: str) -> AssetOut | None:
    row = db.execute(
        select(Asset).where(Asset.ip_address == ip)
    ).scalar_one_or_none()
    return _to_out(row) if row else None


def distinct_owners(db: Session) -> list[str]:
    rows = db.execute(
        select(Asset.business_owner).distinct().order_by(Asset.business_owner)
    ).scalars().all()
    return list(rows)


def distinct_os(db: Session) -> list[str]:
    rows = db.execute(
        select(Asset.operating_system).distinct().order_by(Asset.operating_system)
    ).scalars().all()
    return list(rows)
