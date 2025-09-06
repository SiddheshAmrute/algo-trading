# File: src/algo_trading/db/init_db.py
"""
Async DB initialization utilities for algo-trading.
- Uses SQLModel (async) and asyncpg driver.
- For development convenience we provide create_all; in production use Alembic migrations.
"""
from __future__ import annotations

from typing import Optional

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from ..core.config import get_config

cfg = get_config()
DATABASE_URL = cfg.get_env("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment or config.")

# Create async engine and session factory
_engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[sessionmaker] = None


def get_engine() -> AsyncEngine:
    global _engine, AsyncSessionLocal
    if _engine is None:
        # Example DATABASE_URL: postgresql+asyncpg://user:pass@host:5432/dbname
        _engine = create_async_engine(DATABASE_URL, echo=cfg.get_env("DATABASE_ECHO") in (True, "True", "true"))
        AsyncSessionLocal = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _engine


async def init_db() -> None:
    """
    Create all tables (development only). For production, use Alembic migrations.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# helper async contextmanager for sessions in app code
async def get_session() -> AsyncSession:
    """
    Return a new AsyncSession instance (use: `async with get_session() as session:`).
    Note: this is a simple helper; prefer dependency injection in FastAPI.
    """
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        get_engine()
    async with AsyncSessionLocal() as session:
        yield session
