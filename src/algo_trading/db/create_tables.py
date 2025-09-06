# File: scripts/create_tables.py
"""
Run this script to create all DB tables in the configured DATABASE_URL.
Development helper only — prefer Alembic for production migrations.
Usage:
    python -m scripts.create_tables
"""
import asyncio
import sys
from sqlmodel import SQLModel

from algo_trading.db.init_db import init_db, get_engine
from algo_trading.db import models  # ensure models are imported so metadata is populated


async def _create():
    try:
        await init_db()
        print("✅ All tables created successfully.")
    except Exception as exc:
        print("❌ Table creation failed:", exc)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(_create())
    except Exception:
        sys.exit(1)
