"""
One-time / repeatable ETL: reads the three evidence spreadsheets and loads
them into the assets / av_controls / edr_controls tables.

Usage:
    python scripts/import_data.py \
        --assets /path/asset_inventory.xlsx \
        --av /path/antivirus_evidence.xlsx \
        --edr /path/edr_evidence.xlsx \
        --db-url "mssql+pyodbc://user:pass@myserver/EndpointSecurity?driver=ODBC+Driver+18+for+SQL+Server"

Run sql/schema.sql against the target DB once before the first import.
This script re-runs safely (it replaces each table's contents), so it's
fine to schedule as a recurring job against fresh evidence exports.
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

BOOL_MAPS = {
    "installed": {"Installed": True, "Not Installed": False},
    "onoff": {"Enabled": True, "Disabled": False},
    "yesno": {"Yes": True, "No": False},
}


def _coerce_datetime(series: pd.Series) -> pd.Series:
    """
    pandas usually auto-parses date-formatted Excel cells into datetime64
    on read_excel, but if a cell's number format isn't recognized as a
    date (depends on how the workbook was generated/saved), the column
    comes through as a plain float — an Excel serial date (days since
    1899-12-30) — instead. Detect that case explicitly rather than
    trusting the dtype pandas picked.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    # Not already parsed as datetime — treat as Excel serial date numbers.
    return pd.to_datetime(series, unit="D", origin="1899-12-30", errors="coerce")


def load_assets(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = df.rename(columns={
        "Hostname": "hostname",
        "IP Address": "ip_address",
        "Operating System (OS)": "operating_system",
        "Business Owner": "business_owner",
    })
    before = len(df)
    df = df.dropna(subset=["hostname", "ip_address"])
    if len(df) < before:
        print(f"  WARNING: dropped {before - len(df)} asset row(s) missing hostname/IP", file=sys.stderr)
    dupes = df["hostname"].duplicated().sum()
    if dupes:
        print(f"  WARNING: {dupes} duplicate hostname(s) in asset inventory — keeping last", file=sys.stderr)
        df = df.drop_duplicates(subset=["hostname"], keep="last")
    return df[["hostname", "ip_address", "operating_system", "business_owner"]]


def load_av(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = df.rename(columns={
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
    })
    df["installed"] = df["installed"].map(BOOL_MAPS["installed"])
    df["realtime_protection"] = df["realtime_protection"].map(BOOL_MAPS["onoff"])
    df["tamper_protection"] = df["tamper_protection"].map(BOOL_MAPS["onoff"])
    # Not-installed rows have NaN/NaT everywhere else — that's correct,
    # not a data error, so leave them as NULL rather than filling in.
    return df[["hostname", "installed", "version", "engine_version",
               "signature_version", "last_update", "realtime_protection",
               "tamper_protection", "policy", "last_heartbeat"]]


def load_edr(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = df.rename(columns={
        "Hostname": "hostname",
        "Sensor Installed": "sensor_installed",
        "Sensor Version": "sensor_version",
        "Last Check-in": "last_checkin",
        "Protection Status": "protection_status",
        "Isolation Status": "isolation_status",
        "Policy": "policy",
        "Detection Count": "detection_count",
    })
    df["sensor_installed"] = df["sensor_installed"].map(BOOL_MAPS["yesno"])
    return df[["hostname", "sensor_installed", "sensor_version", "last_checkin",
               "protection_status", "isolation_status", "policy", "detection_count"]]


def report_drift(assets_df, av_df, edr_df):
    asset_hosts = set(assets_df["hostname"])
    av_hosts = set(av_df["hostname"])
    edr_hosts = set(edr_df["hostname"])

    evidence_without_inventory = (av_hosts | edr_hosts) - asset_hosts
    inventory_without_av = asset_hosts - av_hosts
    inventory_without_edr = asset_hosts - edr_hosts

    if evidence_without_inventory:
        print(f"  DRIFT: {len(evidence_without_inventory)} hostname(s) have control evidence "
              f"but are NOT in the asset inventory: {sorted(evidence_without_inventory)}")
    if inventory_without_av:
        print(f"  DRIFT: {len(inventory_without_av)} inventory asset(s) have no AV evidence at all: "
              f"{sorted(inventory_without_av)}")
    if inventory_without_edr:
        print(f"  DRIFT: {len(inventory_without_edr)} inventory asset(s) have no EDR evidence at all: "
              f"{sorted(inventory_without_edr)}")
    if not (evidence_without_inventory or inventory_without_av or inventory_without_edr):
        print("  No drift between inventory and evidence tables.")


def resolve_input_paths(args) -> tuple[str, str, str]:
    if args.assets and args.av and args.edr:
        return args.assets, args.av, args.edr

    search_dirs = []
    if args.folder:
        search_dirs.append(Path(args.folder).expanduser().resolve())
    search_dirs.append(Path(__file__).resolve().parent)
    search_dirs.append(Path.cwd())

    seen_dirs = []
    directories = []
    for directory in search_dirs:
        if directory not in seen_dirs:
            seen_dirs.append(directory)
            directories.append(directory)

    filename_candidates = {
        "assets": ["asset_inventory.xlsx", "asset_inventory.xls", "asset inventory.xlsx", "asset inventory.xls"],
        "av": ["antivirus_evidence.xlsx", "antivirus_evidence.xls", "antivirus evidence.xlsx", "antivirus evidence.xls"],
        "edr": ["edr_evidence.xlsx", "edr_evidence.xls", "edr evidence.xlsx", "edr evidence.xls"],
    }

    def find_in_directory(directory: Path, key: str):
        for filename in filename_candidates[key]:
            candidate = directory / filename
            if candidate.exists():
                return str(candidate)

        for suffix in (".xlsx", ".xls", ".xlsm"):
            for candidate in directory.glob(f"*{suffix}"):
                name = candidate.name.lower()
                if key == "assets" and ("asset" in name or "inventory" in name):
                    return str(candidate)
                if key == "av" and ("av" in name or "antivirus" in name or "evidence" in name):
                    return str(candidate)
                if key == "edr" and ("edr" in name or "evidence" in name):
                    return str(candidate)
        return None

    resolved = {}
    for key in ("assets", "av", "edr"):
        for directory in directories:
            if not directory.exists():
                continue
            found = find_in_directory(directory, key)
            if found:
                resolved[key] = found
                break
        if key not in resolved:
            searched = ", ".join(str(directory) for directory in directories)
            raise FileNotFoundError(
                f"Could not find {key} spreadsheet in any of: {searched}. Expected one of: {', '.join(filename_candidates[key])}"
            )

    return resolved["assets"], resolved["av"], resolved["edr"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets")
    parser.add_argument("--av")
    parser.add_argument("--edr")
    parser.add_argument("--folder",
                         help="Folder containing asset_inventory.xlsx, antivirus_evidence.xlsx, and edr_evidence.xlsx")
    parser.add_argument("--db-url", required=True,
                         help="SQLAlchemy connection URL, e.g. "
                              "mssql+pyodbc://user:pass@server/db?driver=ODBC+Driver+18+for+SQL+Server")
    args = parser.parse_args()

    try:
        assets_path, av_path, edr_path = resolve_input_paths(args)
    except FileNotFoundError as exc:
        parser.error(str(exc))

    print("Reading spreadsheets...")
    assets_df = load_assets(assets_path)
    av_df = load_av(av_path)
    edr_df = load_edr(edr_path)

    print("Checking inventory/evidence drift...")
    report_drift(assets_df, av_df, edr_df)

    print(f"Loading into {args.db_url.split('@')[-1] if '@' in args.db_url else args.db_url}...")
    engine = create_engine(args.db_url)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM assets"))
        conn.execute(text("DELETE FROM av_controls"))
        conn.execute(text("DELETE FROM edr_controls"))

    assets_df.to_sql("assets", engine, if_exists="append", index=False)
    av_df.to_sql("av_controls", engine, if_exists="append", index=False)
    edr_df.to_sql("edr_controls", engine, if_exists="append", index=False)

    print(f"Loaded {len(assets_df)} assets, {len(av_df)} AV records, {len(edr_df)} EDR records.")


if __name__ == "__main__":
    main()