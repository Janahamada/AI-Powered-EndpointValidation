"""
Create all tables from the ORM models (single schema source of truth).

Usage:
    python backend/scripts/init_db.py            # create missing tables
    python backend/scripts/init_db.py --drop     # drop + recreate everything

The ORM models in app/db_models are the authoritative schema; there is no
separate hand-maintained DDL file to drift from.
"""

import argparse

import _bootstrap  # noqa: F401  (side-effect: sys.path)

from app.config import settings
from app.database import Base, engine
import app.db_models  # noqa: F401  (registers all models on Base.metadata)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all tables before recreating (wipes data).",
    )
    args = parser.parse_args()

    if args.drop:
        Base.metadata.drop_all(bind=engine)
        print("Dropped all tables.")

    Base.metadata.create_all(bind=engine)
    tables = ", ".join(sorted(Base.metadata.tables))
    print(f"Initialized schema at {settings.DATABASE_URL}")
    print(f"Tables: {tables}")


if __name__ == "__main__":
    main()
