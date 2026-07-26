"""
ETL: load the five evidence sources into the database.

  assets  <- scripts/asset_inventory.xlsx      (CORP-* hostnames)
  av      <- scripts/antivirus_evidence.xlsx   (CORP-* hostnames)
  edr     <- scripts/edr_evidence.xlsx         (CORP-* hostnames)
  fw      <- firewall_telemetry.csv            (WORKSTATION-NNN -> re-keyed)
  bl      <- bitlocker_telemetry.csv           (WORKSTATION-NNN -> re-keyed)

Firewall & BitLocker telemetry are keyed by generic 'WORKSTATION-NNN' names
with no shared key to the CORP asset inventory. Per the agreed design we
POSITIONALLY re-key them: the telemetry rows (sorted by their numeric suffix)
are mapped onto the CORP asset hostnames (sorted), so every asset unifies all
four controls under its CORP hostname. Any telemetry rows beyond the number of
assets are reported as drift and dropped. This is a documented synthetic
mapping, not a claim that the source systems share identity.

    python backend/scripts/import_data.py

Re-runs safely (replaces each table's contents).
"""

import re
import sys

import _bootstrap  # noqa: F401
import pandas as pd

from app.config import REPO_ROOT
from app.database import SessionLocal
from app.db_models import (
    Asset,
    AvControl,
    BitlockerControl,
    EdrControl,
    FirewallControl,
)

# Source file locations (repo root).
SCRIPTS_DIR = REPO_ROOT / "scripts"
ASSETS_XLSX = SCRIPTS_DIR / "asset_inventory.xlsx"
AV_XLSX = SCRIPTS_DIR / "antivirus_evidence.xlsx"
EDR_XLSX = SCRIPTS_DIR / "edr_evidence.xlsx"
FW_CSV = REPO_ROOT / "firewall_telemetry.csv"
BL_CSV = REPO_ROOT / "bitlocker_telemetry.csv"

_BOOL_INSTALLED = {"Installed": 1, "Not Installed": 0}
_BOOL_ONOFF = {"Enabled": 1, "Disabled": 0}
_BOOL_YESNO = {"Yes": 1, "No": 0}
_WORKSTATION_NUM = re.compile(r"(\d+)")


def _dt_to_iso(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        return value
    return pd.Timestamp(value).isoformat(sep=" ")


def _num(name: str) -> int:
    m = _WORKSTATION_NUM.search(str(name))
    return int(m.group(1)) if m else 0


# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #
def load_assets() -> list[dict]:
    df = pd.read_excel(ASSETS_XLSX).rename(
        columns={
            "Hostname": "hostname",
            "IP Address": "ip_address",
            "Operating System (OS)": "operating_system",
            "Business Owner": "business_owner",
        }
    )
    df = df.dropna(subset=["hostname", "ip_address"]).drop_duplicates(
        subset=["hostname"], keep="last"
    )
    return df[
        ["hostname", "ip_address", "operating_system", "business_owner"]
    ].to_dict("records")


def load_av() -> list[dict]:
    df = pd.read_excel(AV_XLSX).rename(
        columns={
            "Hostname": "hostname",
            "Installed": "installed",
            "Version": "version",
            "Engine Version": "engine_version",
            "Signature Version": "signature_version",
            "Last Update": "last_update",
            "Real-Time Protection": "realtime_protection",
            "Tamper Protection": "tamper_protection",
            "Policy": "policy",
            "Last Heartbeat": "last_heartbeat",
        }
    )
    rows = []
    for r in df.to_dict("records"):
        rows.append(
            dict(
                hostname=r["hostname"],
                installed=_BOOL_INSTALLED.get(r.get("installed"), 0),
                version=_clean(r.get("version")),
                engine_version=_clean(r.get("engine_version")),
                signature_version=_clean(r.get("signature_version")),
                last_update=_dt_to_iso(r.get("last_update")),
                realtime_protection=_BOOL_ONOFF.get(r.get("realtime_protection"), 0),
                tamper_protection=_BOOL_ONOFF.get(r.get("tamper_protection"), 0),
                policy=_clean(r.get("policy")),
                last_heartbeat=_dt_to_iso(r.get("last_heartbeat")),
            )
        )
    return rows


def load_edr() -> list[dict]:
    df = pd.read_excel(EDR_XLSX).rename(
        columns={
            "Hostname": "hostname",
            "Sensor Installed": "sensor_installed",
            "Sensor Version": "sensor_version",
            "Last Check-in": "last_checkin",
            "Protection Status": "protection_status",
            "Isolation Status": "isolation_status",
            "Policy": "policy",
            "Detection Count": "detection_count",
        }
    )
    rows = []
    for r in df.to_dict("records"):
        rows.append(
            dict(
                hostname=r["hostname"],
                sensor_installed=_BOOL_YESNO.get(r.get("sensor_installed"), 0),
                sensor_version=_clean(r.get("sensor_version")),
                last_checkin=_dt_to_iso(r.get("last_checkin")),
                protection_status=_clean(r.get("protection_status")) or "Unknown",
                isolation_status=_clean(r.get("isolation_status")) or "Unknown",
                policy=_clean(r.get("policy")),
                detection_count=int(r.get("detection_count") or 0),
            )
        )
    return rows


def load_fw_raw() -> list[dict]:
    df = pd.read_csv(FW_CSV)
    return sorted(
        (
            dict(
                device=r["Device_Name"],
                domain_profile=_clean(r.get("Domain")),
                private_profile=_clean(r.get("Private")),
                public_profile=_clean(r.get("Public")),
                default_inbound_action=_clean(r.get("DefaultInboundAction")),
            )
            for r in df.to_dict("records")
        ),
        key=lambda d: _num(d["device"]),
    )


def load_bl_raw() -> list[dict]:
    df = pd.read_csv(BL_CSV)
    return sorted(
        (
            dict(
                device=r["deviceName"],
                encryption_method=_clean(r.get("Encryption_Method")),
                protection_status=_clean(r.get("Protection_Status")),
                percentage_encrypted=int(r.get("Percentage_Encrypted") or 0),
                volume_status=_clean(r.get("Volume_Status")),
                is_encrypted=1 if str(r.get("isEncrypted")).strip().lower() == "true" else 0,
                compliance_state=_clean(r.get("complianceState")),
            )
            for r in df.to_dict("records")
        ),
        key=lambda d: _num(d["device"]),
    )


def _clean(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return s or None


# --------------------------------------------------------------------------- #
# Positional re-key
# --------------------------------------------------------------------------- #
def rekey(raw_rows: list[dict], asset_hostnames: list[str], label: str) -> list[dict]:
    """Map telemetry rows (already numeric-sorted) onto sorted CORP hostnames."""
    mapped = []
    for row, hostname in zip(raw_rows, asset_hostnames):
        row = dict(row)
        row["hostname"] = hostname
        row.pop("device", None)
        mapped.append(row)
    leftover = len(raw_rows) - len(asset_hostnames)
    if leftover > 0:
        dropped = [r["device"] for r in raw_rows[len(asset_hostnames):]]
        print(
            f"  DRIFT: {leftover} {label} telemetry row(s) had no asset to map onto "
            f"and were dropped: {dropped}"
        )
    return mapped


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    print("Reading sources...")
    assets = load_assets()
    av = load_av()
    edr = load_edr()
    fw_raw = load_fw_raw()
    bl_raw = load_bl_raw()

    asset_hostnames = sorted(a["hostname"] for a in assets)
    print(
        f"  assets={len(assets)} av={len(av)} edr={len(edr)} "
        f"firewall={len(fw_raw)} bitlocker={len(bl_raw)}"
    )

    # Drift: AV/EDR evidence for hostnames not in inventory.
    asset_set = set(asset_hostnames)
    for name, rows in (("AV", av), ("EDR", edr)):
        orphan = sorted(r["hostname"] for r in rows if r["hostname"] not in asset_set)
        if orphan:
            print(f"  DRIFT: {len(orphan)} {name} evidence host(s) not in inventory: {orphan}")

    print("Positionally re-keying firewall/bitlocker onto CORP hostnames...")
    fw = rekey(fw_raw, asset_hostnames, "firewall")
    bl = rekey(bl_raw, asset_hostnames, "bitlocker")

    print("Loading into database (replacing existing contents)...")
    with SessionLocal() as db:
        for model in (
            AvControl,
            EdrControl,
            FirewallControl,
            BitlockerControl,
            Asset,
        ):
            db.query(model).delete()
        db.bulk_insert_mappings(Asset.__mapper__, assets)
        db.bulk_insert_mappings(AvControl.__mapper__, av)
        db.bulk_insert_mappings(EdrControl.__mapper__, edr)
        db.bulk_insert_mappings(FirewallControl.__mapper__, fw)
        db.bulk_insert_mappings(BitlockerControl.__mapper__, bl)
        db.commit()

    print(
        f"Loaded {len(assets)} assets, {len(av)} AV, {len(edr)} EDR, "
        f"{len(fw)} firewall, {len(bl)} bitlocker records."
    )


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(f"ERROR: missing source file — {exc}", file=sys.stderr)
        sys.exit(1)
