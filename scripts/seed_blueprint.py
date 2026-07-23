"""
Seeds (or re-seeds) the blueprint_rules table with the default rule set.

Run once after init_sqlite_db.py:
    python scripts/seed_blueprint.py

Safe to re-run — it replaces the table contents. If you've hand-edited
rules directly in the DB and want to keep those edits, don't re-run this;
edit the table directly instead (that's the whole point of moving it
into the DB).
"""

import json
import os
import sys

from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL

# Same rules that used to live hardcoded in db/blueprint.py.
DEFAULT_RULES = [
    dict(field="av_installed", operator="eq", expected=True,
         severity="critical", description="Antivirus must be installed."),
    dict(field="av_version", operator="gte", expected="4.18.24050.7",
         severity="medium", description="Antivirus version must be at least 4.18.24050.7."),
    dict(field="av_realtime_protection", operator="eq", expected=True,
         severity="critical", description="AV real-time protection must be enabled."),
    dict(field="av_tamper_protection", operator="eq", expected=True,
         severity="high", description="AV tamper protection must be enabled."),
    dict(field="av_policy", operator="eq", expected="Standard_Workstation_Policy",
         severity="medium", description="AV policy must be set to 'Standard_Workstation_Policy'."),
    dict(field="av_signature_age_days", operator="lte", expected=7,
         severity="high", description="AV signatures must be updated within 7 days."),
    dict(field="edr_sensor_installed", operator="eq", expected=True,
         severity="critical", description="EDR sensor must be installed."),
    dict(field="edr_sensor_version", operator="gte", expected="6.55.18203",
         severity="medium", description="EDR sensor version must be at least 6.55.18203."),
    dict(field="edr_protection_status", operator="eq", expected="Healthy",
         severity="critical", description="EDR sensor must report a healthy protection status."),
    dict(field="edr_isolation_status", operator="eq", expected="Not Isolated",
         severity="high", description="EDR sensor must not be isolated."),
    dict(field="edr_policy", operator="eq", expected="EDR_Production_v2",
         severity="medium", description="EDR policy must be set to 'EDR_Production_v2'."),
    dict(field="edr_last_checkin_hours", operator="lte", expected=24,
         severity="medium", description="EDR agent must check in at least every 24 hours."),
]


def main():
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM blueprint_rules"))
        conn.execute(text("DELETE FROM sqlite_sequence WHERE name = 'blueprint_rules'"))
        for rule in DEFAULT_RULES:
            conn.execute(
                text("""INSERT INTO blueprint_rules (field, operator, expected, severity, description)
                        VALUES (:field, :operator, :expected, :severity, :description)"""),
                {**rule, "expected": json.dumps(rule["expected"])},
            )
    print(f"Seeded {len(DEFAULT_RULES)} blueprint rule(s).")


if __name__ == "__main__":
    main()
