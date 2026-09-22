import os
import ssl
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# SSL context (Neon PostgreSQL uchun)
connect_args = {}
if DATABASE_URL and "neon.tech" in DATABASE_URL:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

# Async Engine - Serverless (Vercel) uchun moslashtirilgan
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Production uchun False ma'qul
    connect_args=connect_args,
    pool_pre_ping=True,  # O'lik ulanishlarni avtomatik qayta tiklaydi (MUHIM!)
    pool_recycle=300,    # 5 minutdan oshgan ulanishlarni yangilaydi
    # Vercel Serverless'da ulanishlar to'planib qolmasligi uchun NullPool tavsiya etiladi:
    # poolclass=NullPool 
)

# Aiogram Middleware va FastAPI uchun Session Maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

# FastAPI endpointlari uchun (agar kerak bo'lsa)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise