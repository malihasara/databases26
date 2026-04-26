"""
api/index.py

Vercel serverless entrypoint. Loads the Flask app from backend/api/index.py.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.api.index import app  # noqa: E402
