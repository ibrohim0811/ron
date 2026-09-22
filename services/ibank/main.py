import os
import json
import random
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from upstash_redis import Redis
from dotenv import load_dotenv
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

load_dotenv()

dp = Router()

redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL", "https://humorous-beagle-289672.upstash.io"), 
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
)

def service_phone_request() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Telefon raqamni ulashish 📲", request_contact=True)]
        ], 
        resize_keyboard=True,
        one_time_keyboard=True
    )

@dp.message(Command('start'))
async def get_startdata(msg: types.Message, command: CommandObject):
    # start bilan kelgan parametrni olamiz (masalan: jamgarmauz)
    source_app = command.args if command.args == "jamgarmauz" else "direct"
    user_id = msg.from_user.id

    # Vaqtinchalik app nomini user_id bo'yicha saqlab turamiz (10 minut)
    redis.set(f"temp_source:{user_id}", source_app, ex=600)

    await msg.answer(
        f"Assalomu alaykum {msg.from_user.first_name}, RON by IDEV 🤖 ga xush kelibsiz 👋\n"
        f"Pastdagi tugma orqali Telefon raqamingizni yuboring 👇\n"
        f"Eslatma: Jamg'arma ilovasida ro'yxatdan o'tilgan raqam bilan bir xil bo'lishi shart ‼️", 
        reply_markup=service_phone_request()
    )

@dp.message(F.contact)
async def get_phone(msg: types.Message):
    phone_number = msg.contact.phone_number
    # Telefon raqam boshida '+' bo'lmasa, qo'shib qo'yamiz
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    telegram_id = msg.from_user.id

    # Oldinroq saqlangan app nomini olamiz
    source_app = redis.get(f"temp_source:{telegram_id}") or "unknown"

    # 6 xonalik OTP kod generatsiya qilamiz
    otp_code = str(random.randint(100000, 999999))

    # Redis'ga yuboriladigan umumiy ma'lumot
    data_payload = {
        "otp": otp_code,
        "app": source_app,
        "telegram_id": telegram_id,
        "phone_number": phone_number
    }

    # Redis'ga saqlash (Key: "otp:+998901234567", TTL: 180 soniya)
    redis.set(
        f"otp:{phone_number}", 
        json.dumps(data_payload), 
        ex=180
    )

    await msg.answer(
        f"Sizning tasdiqlash kodingiz: {otp_code}\n"
        f"Kod 3 daqiqa davomida amal qiladi."
    )


