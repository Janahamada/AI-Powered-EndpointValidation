"""
Evidence provenance.

Answers "where did this value come from?" for a single endpoint: which source
file each control's evidence was ingested from, when it was loaded, and whether
a row exists at all. Read-only reporting over the evidence tables — it performs
no validation and is never consulted by the compliance engine.

The source filenames mirror `backend/scripts/import_data.py`; if the ETL's
inputs change, update them here too.
"""

from sqlalchemy.orm import Session

from app.db_models import Asset, AvControl, BitlockerControl, DlpControl, EdrControl

#: control_type -> (ORM model, source file as loaded by the ETL)
_SOURCES: dict[str, tuple[type, str]] = {
    "antivirus": (AvControl, "scripts/antivirus_evidence.xlsx"),
    "edr": (EdrControl, "scripts/edr_evidence.xlsx"),
    "dlp": (DlpControl, "dlp_telemetry.csv"),
    "bitlocker": (BitlockerControl, "bitlocker_telemetry.csv"),
}


def evidence_sources(db: Session, hostname: str) -> list[dict]:
    """One provenance entry per control, plus the asset inventory itself."""
    out: list[dict] = []

    asset = db.get(Asset, hostname)
    out.append(
        {
            "control_type": "asset",
            "label": "Asset inventory",
            "source_file": "scripts/asset_inventory.xlsx",
            "loaded_at": getattr(asset, "loaded_at", None),
            "present": asset is not None,
            "key": hostname,
        }
    )

    for control_type, (model, source_file) in _SOURCES.items():
        row = db.get(model, hostname)
        out.append(
            {
                "control_type": control_type,
                "label": control_type,
                "source_file": source_file,
                "loaded_at": getattr(row, "loaded_at", None),
                "present": row is not None,
                "key": hostname,
            }
        )
    return out
