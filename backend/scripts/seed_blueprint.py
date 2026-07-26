"""
Seed (or re-seed) the blueprint_rules table with the default assurance
baseline for all four controls.

    python backend/scripts/seed_blueprint.py

Safe to re-run — it replaces the table contents. The AV/EDR rules match the
original baseline; the Firewall/BitLocker rules are derived from the
golden-image reference rows in firewall_blueprint.csv / bitlocker_blueprint.csv.
"""

import json

import _bootstrap  # noqa: F401

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.db_models import BlueprintRule
from app.services.blueprint_defaults import DEFAULT_RULES


def seed(db: Session) -> int:
    db.execute(delete(BlueprintRule))
    for rule in DEFAULT_RULES:
        db.add(
            BlueprintRule(
                control_type=rule["control_type"],
                field=rule["field"],
                operator=rule["operator"],
                expected=json.dumps(rule["expected"]),
                severity=rule["severity"],
                description=rule["description"],
            )
        )
    db.commit()
    return len(DEFAULT_RULES)


def main() -> None:
    with SessionLocal() as db:
        n = seed(db)
    print(f"Seeded {n} blueprint rule(s) across antivirus/edr/firewall/bitlocker.")


if __name__ == "__main__":
    main()
