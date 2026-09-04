import sys
from pathlib import Path

# Add workspace root to sys.path so modules resolve correctly on Vercel
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.database.schema import init_db

# Eagerly initialize SQLite schema and seed dataset on serverless container boot
try:
    init_db(seed=True)
except Exception as e:
    print(f"Serverless DB init notice: {e}")

from app import app
