"""Script to ingest both policy collections into Chroma.

Run from the `backend/` folder:

    python scripts/ingest_policies.py

This calls `ingest_policies` for `policies/master_policies` and
`policies/standards` and prints the number of files indexed.
"""

import _bootstrap  # noqa: F401
from app.config import settings
from app.rag.retriever import ingest_policies
from pathlib import Path

root = Path(settings.POLICIES_ROOT)
master = root / "master_policies"
standards = root / "standards"

print('Ingesting policies into Chroma at', settings.CHROMA_PATH)
print('Master policies dir:', master)
print('Standards dir:', standards)

m = ingest_policies(str(master), collection_key="master_policies")
s = ingest_policies(str(standards), collection_key="standards")
print(f"Ingested {m} master policy files and {s} standards files.")
