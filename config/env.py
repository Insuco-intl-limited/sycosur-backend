# config/env.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
PROD_ENV_FILE = BASE_DIR / ".envs" / ".env.local"