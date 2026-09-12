from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram_i18n import I18nContext

def phone_number_request(i18n: I18nContext) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n("share_phone"), request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

