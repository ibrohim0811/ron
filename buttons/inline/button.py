from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram_i18n import I18nContext



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

def main_menu(i18n: I18nContext) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=i18n("settings"), callback_data="settings"),
                InlineKeyboardButton(text=i18n("projects"), callback_data="projects"),
            ],
            [
                InlineKeyboardButton(text=i18n("transactions"), callback_data="transactions")
            ],
            [
                InlineKeyboardButton(text=i18n("help"), callback_data="help"),
                InlineKeyboardButton(text=i18n("about_us"), callback_data="about_us"),
            ],
            [
                InlineKeyboardButton(text=i18n("our_projects"), callback_data="our_projects")
            ]
        ]
    )
