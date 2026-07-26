"""Blueprint rule data access. `expected` is JSON-decoded to its real type."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import BlueprintRule
from app.schemas.control import BlueprintRuleOut


def get_all(db: Session) -> list[BlueprintRuleOut]:
    rows = db.execute(select(BlueprintRule).order_by(BlueprintRule.id)).scalars().all()
    return [
        BlueprintRuleOut(
            control_type=row.control_type,
            field=row.field,
            operator=row.operator,
            expected=json.loads(row.expected),  # restores bool/int/str type
            severity=row.severity,
            description=row.description,
        )
        for row in rows
    ]
