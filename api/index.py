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

load_dotenv()

from middleware.i18n import i18n_middleware
from core.database import engine, Base
from middleware.db import DbSessionMiddleware
from buttons.inline.button import language_button, main_menu
from crud.register import get_user_by_telegram_id
from routers.register import dp as register
from routers.menu import dp as menu

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Masalan: https://loyiha-nomi.vercel.app/api/webhook

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher(storage=MemoryStorage())

# Middleware va Routerlar
i18n_middleware.setup(dispatcher=dp)
dp.update.outer_middleware(DbSessionMiddleware())

dp.include_router(register)
dp.include_router(menu)

# Redis xavfsiz boshlang'ich sozlamalari
UPSTASH_TOKEN = os.getenv("UPSTASH_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN")
UPSTASH_URL = os.getenv("UPSTASH_URL") or os.getenv("UPSTASH_REDIS_REST_URL")

redis = None
if UPSTASH_URL and UPSTASH_TOKEN:
    try:
        from upstash_redis import Redis
        redis = Redis(url=UPSTASH_URL, token=UPSTASH_TOKEN)
    except Exception as e:
        logger.warning(f"Upstash Redis ulanishida ogohlantirish: {e}")


@dp.message(CommandStart(deep_link=True))
async def start_deep_link_handler(message: types.Message, command: CommandObject):
    if not redis:
        await message.answer("Redis sozlanmagan. FSM /register orqali qaytadan urining.")
        return

    phone = command.args.strip()
    if not phone.startswith("+"):
        phone = "+" + phone.lstrip()

    try:
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
    except Exception as e:
        logger.error(f"Deep link processing error: {e}")
        await message.answer("Xatolik yuz berdi. Qayta urinib ko'ring.")


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
    # Lifespan: Baza jadvallarini yaratish/tekshirish
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables successfully checked/created.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    # Webhook-ni avtomatik tekshirish va o'rnatish
    if bot and WEBHOOK_URL:
        try:
            current_info = await bot.get_webhook_info()
            if current_info.url != WEBHOOK_URL:
                await bot.set_webhook(url=WEBHOOK_URL)
                logger.info(f"Webhook set to {WEBHOOK_URL}")
        except Exception as e:
            logger.error(f"Error setting webhook on lifespan start: {e}")
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/api/webhook")
async def webhook(request: Request):
    if not bot:
        return {"status": "error", "message": "BOT_TOKEN is missing"}
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logger.exception("Error handling webhook update")
        return {"status": "error", "message": str(e)}


@app.get("/api/set_webhook")
@app.get("/set_webhook")
async def set_webhook():
    if not bot:
        return {"ok": False, "error": "BOT_TOKEN missing in environment variables"}
    if not WEBHOOK_URL:
        return {"ok": False, "error": "WEBHOOK_URL missing in environment variables"}
    try:
        res = await bot.set_webhook(url=WEBHOOK_URL)
        info = await bot.get_webhook_info()
        return {
            "ok": res,
            "webhook_url": info.url,
            "pending_update_count": info.pending_update_count,
            "last_error_message": info.last_error_message
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/")
async def root():
    webhook_info = None
    if bot:
        try:
            info = await bot.get_webhook_info()
            webhook_info = {
                "url": info.url,
                "pending_update_count": info.pending_update_count,
                "last_error_date": info.last_error_date,
                "last_error_message": info.last_error_message
            }
        except Exception:
            pass
    return {
        "status": "bot is running",
        "webhook_url_env": WEBHOOK_URL,
        "webhook_info": webhook_info
    }