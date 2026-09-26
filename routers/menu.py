from aiogram import Router, types, F
from aiogram_i18n import I18nContext

from buttons.inline.button import back_to_menu_button, main_menu

dp = Router()

# Maps each main-menu callback_data to the locale key holding its content.
# (Previously none of these had a handler at all, so tapping any of them
# just left the button spinning until Telegram gave up.)
_SECTION_TEXT_KEYS = {
    "settings": "settings_text",
    "projects": "projects_text",
    "transactions": "transactions_text",
    "help": "help_text",
    "about_us": "about_us_text",
    "our_projects": "our_projects_text",
}


@dp.callback_query(F.data.in_(_SECTION_TEXT_KEYS.keys()))
async def open_menu_section(call: types.CallbackQuery, i18n: I18nContext):
    text_key = _SECTION_TEXT_KEYS[call.data]
    await call.message.edit_text(i18n(text_key), reply_markup=back_to_menu_button(i18n))
    await call.answer()


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: types.CallbackQuery, i18n: I18nContext):
    await call.message.edit_text(f"{i18n('main')}\n{i18n('select_menu')}", reply_markup=main_menu(i18n=i18n))
    await call.answer()
