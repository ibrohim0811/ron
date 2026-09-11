from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def language_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="O'zbekcha 🇺🇿", callback_data="uz"),
                InlineKeyboardButton(text="Русский 🇷🇺", callback_data="ru"),
                InlineKeyboardButton(text="English 🇺🇸", callback_data="en")
            ]
        ]
    )
