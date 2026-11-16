import os
import sys
from pathlib import Path

# Ensure root and backend directories are on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app import app

# Export WSGI application for Vercel Serverless Function
if __name__ == "__main__":
    app.run()
