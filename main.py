import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReactionTypeEmoji
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from aiogram_i18n import I18nContext
from upstash_redis import Redis

load_dotenv()

from middleware.i18n import i18n_middleware
from core.database import engine, Base
from middleware.db import DbSessionMiddleware
from buttons.inline.button import language_button, main_menu
from crud.register import get_user_by_telegram_id
from routers.register import dp as register
from routers.menu import dp as menu

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") # Masalan: https://loyiha-nomi.vercel.app/api/webhook

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Middleware va Routerlar
i18n_middleware.setup(dispatcher=dp)
dp.update.outer_middleware(DbSessionMiddleware())

dp.include_router(register)
dp.include_router(menu)

UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN")
UPSTASH_URL = os.getenv("UPSTASH_URL")
redis = Redis(url=UPSTASH_URL, token=UPSTASH_TOKEN)


@dp.message(CommandStart(deep_link=True))
async def start_deep_link_handler(message: types.Message, command: CommandObject):
    phone = command.args.strip()
    if not phone.startswith("+"):
        phone = "+" + phone.lstrip()

    raw = redis.get(f"otp:{phone}")
    if not raw:
        await message.answer("Kod topilmadi yoki muddati o'tgan. FSM /register orqali qaytadan urining.")
        return
        
    data = json.loads(raw)
    await message.answer(
        f"Xush kelibsiz, {data.get('full_name')}!\n"
        f"Tasdiqlash kodingiz: `{data['otp_code']}`",
        parse_mode="Markdown"
    )


@dp.message(Command('start'))
async def start(msg: types.Message, i18n: I18nContext, db: AsyncSession):
    user = await get_user_by_telegram_id(db, msg.from_user.id)
    if user is not None:
        await i18n.set_locale(user.language)
        await msg.answer(f"{i18n('welcome')} {user.full_name}")
        await msg.answer(f"{i18n('main')} \n{i18n('select_menu')}", reply_markup=main_menu(i18n=i18n))
        return

    await msg.react(reaction=[ReactionTypeEmoji(emoji="⚡")])
    await msg.answer(
        f"Assalomu alaykum {msg.from_user.first_name} Botimizga xush kelibsiz 👋\n"
        "🇺🇿 Tilni tanlang:\n🇷🇺 Выберите язык:\n🇺🇸 Choose language:", 
        reply_markup=language_button()
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lifespan: Webhook o'rnatish va bazani ishga tushirish
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    if WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL)
    yield
    await bot.delete_webhook()

app = FastAPI(lifespan=lifespan)


@app.post("/api/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot, update)
    return {"status": "ok"}