"""
Initializes the local SQLite database from sql/schema_sqlite.sql.
Run once (or any time you want to wipe and recreate the schema):

    python scripts/init_sqlite_db.py

Doesn't touch config.py's DATABASE_URL — reads it directly, so it always
targets whatever DB file your config currently points at.
"""

import os
import re
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "schema_sqlite.sql")


def main():
    if not DATABASE_URL.startswith("sqlite:///"):
        print(f"DATABASE_URL is '{DATABASE_URL}', not a sqlite:/// URL — "
              "this script only initializes SQLite. For SQL Server, run "
              "sql/schema.sql with sqlcmd instead.", file=sys.stderr)
        sys.exit(1)

    db_path = DATABASE_URL.replace("sqlite:///", "", 1)

    with open(SCHEMA_PATH) as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    print(f"Initialized schema in {db_path}")


if __name__ == "__main__":
    main()
