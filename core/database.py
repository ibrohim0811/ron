import os
import ssl
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Ensure asyncpg driver is specified for PostgreSQL URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# SSL context (for Neon PostgreSQL or Supabase)
connect_args = {}
if DATABASE_URL and ("neon.tech" in DATABASE_URL or "supabase" in DATABASE_URL or "sslmode=require" in DATABASE_URL):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

# Engine configuration optimized for Vercel Serverless
engine_kwargs = {
    "echo": False,
    "connect_args": connect_args,
    "pool_pre_ping": True,
}

# Use NullPool in serverless environments to avoid stale connections
if os.getenv("VERCEL") or os.getenv("SERVERLESS"):
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_recycle"] = 300

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise