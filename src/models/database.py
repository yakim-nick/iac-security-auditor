from __future__ import annotations

import asyncpg
from src.config import settings

_pool: asyncpg.Pool | None = None


async def init_db():
    """Create the connection pool and ensure the audits table exists."""
    global _pool
    # asyncpg only accepts a plain postgres:// DSN, not SQLAlchemy's +asyncpg scheme.
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                id SERIAL PRIMARY KEY,
                repo TEXT NOT NULL,
                ref TEXT NOT NULL,
                commit_sha TEXT,
                status TEXT DEFAULT 'pending',
                findings JSONB DEFAULT '[]'::jsonb,
                pr_number INT,
                created_at TIMESTAMPTZ DEFAULT now()
            );
        """)


async def close_db():
    """Close the connection pool; called on application shutdown."""
    global _pool
    if _pool:
        await _pool.close()


async def get_pool() -> asyncpg.Pool:
    """Return the initialized pool, raising if init_db was never called."""
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool
