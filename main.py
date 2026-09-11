import os
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram import types
from aiogram.types import ReactionTypeEmoji
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from aiogram_i18n import I18nContext

load_dotenv()

from middleware.i18n import i18n_middleware
from core.database import engine, Base
from middleware.db import DbSessionMiddleware
from buttons.inline.button import language_button
from crud.register import get_user_by_telegram_id
from routers.register import dp as register

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Middleware'larni sozlash
i18n_middleware.setup(dispatcher=dp)
dp.update.outer_middleware(DbSessionMiddleware())

# Routerlarni ulash
dp.include_router(register)


@dp.message(Command('start'))
async def start(msg: types.Message, i18n: I18nContext, db: AsyncSession):
    user = await get_user_by_telegram_id(db, msg.from_user.id)
    
    # Agar foydalanuvchi bazada mavjud bo'lsa
    if user is not None:
        await i18n.set_locale(user.language)
        await msg.answer(f"{i18n('welcome')} {user.full_name}")
        return  # Qaytadan til so'ramasligi uchun tugatamiz

    # Yangi foydalanuvchilar uchun
    await msg.react(reaction=[ReactionTypeEmoji(emoji="⚡")])
    await msg.answer(
        f"Assalomu alaykum {msg.from_user.first_name} Botimizga xush kelibsiz 👋\n"
        "🇺🇿 Tilni tanlang:\n🇷🇺 Выберите язык:\n🇺🇸 Choose language:", 
        reply_markup=language_button()
    )


async def init_db():
    """Bazada jadvallarni yaratish"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    # 1. Baza jadvallarini yaratamiz (bitta loop ichida)
    await init_db()
    print("Migrations applied all is ok 🟢")
    
    # 2. Botni polling rejimida ishga tushiramiz
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Faqat BIR MARTA asyncio.run() chaqiriladi!
    asyncio.run(main())