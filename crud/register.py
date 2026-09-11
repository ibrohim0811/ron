from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User


# --- GET (Foydalanuvchilarni olish) ---

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    """Telegram ID bo'yicha bitta foydalanuvchini olish"""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """Baza ID'si bo'yicha bitta foydalanuvchini olish"""
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_all_users(session: AsyncSession) -> Sequence[User]:
    """Barcha foydalanuvchilar ro'yxatini olish"""
    stmt = select(User).order_by(User.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


# --- POST (Yangi foydalanuvchi yaratish) ---

async def create_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    phone_number: str,
    language: str = "uz"
) -> User:
    existing_user = await get_user_by_telegram_id(session, telegram_id)
    if existing_user:
        return existing_user

    new_user = User(
        telegram_id=telegram_id,
        full_name=full_name,
        phone_number=phone_number,
        language=language
    )
    session.add(new_user)
    
    # Bazaga doimiy saqlash uchun commit qilamiz
    await session.commit()
    
    # obyekt ma'lumotlarini yangilab olish uchun (masalan id va created_at)
    await session.refresh(new_user) 
    
    return new_user