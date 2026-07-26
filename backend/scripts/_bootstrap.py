"""
Shared path bootstrap for the standalone scripts.

Importing this puts `backend/` on sys.path so `import app...` resolves when a
script is run directly (e.g. `python backend/scripts/init_db.py`).
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
