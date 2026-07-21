"""
get_blueprint() keeps the exact same signature and return type
(list[BlueprintRule]) as before, so compliance/comparator.py and
everything downstream is untouched.
"""

import json
import os
import sys

from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL
from models import BlueprintRule

_engine = create_engine(DATABASE_URL)


def get_blueprint() -> list[BlueprintRule]:
    with _engine.connect() as conn:
        rows = conn.execute(
            text("SELECT field, operator, expected, severity, description "
                 "FROM blueprint_rules ORDER BY id")
        ).mappings().fetchall()

    return [
        BlueprintRule(
            field=row["field"],
            operator=row["operator"],
            expected=json.loads(row["expected"]),  # restores bool/int/str type
            severity=row["severity"],
            description=row["description"],
        )
        for row in rows
    ]
