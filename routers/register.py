from aiogram import Router, types, F
from aiogram_i18n import I18nContext
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from states.register import Register
from buttons.keyboard.button import phone_number_request
from validation import is_valid_uz_phone
from crud.register import create_user

dp = Router()


# 1. Til tanlash
@dp.callback_query(F.data.in_({"uz", "en", "ru"}))
async def change_language(call: types.CallbackQuery, i18n: I18nContext, state: FSMContext):
    lang = call.data
    await state.update_data(language=lang)
    await i18n.set_locale(lang)
    
    await state.set_state(Register.full_name)
    
    # Callback kelgan xabarning o'zini edit qilamiz (Ism so'rash xabariga aylantiramiz)
    await call.message.edit_text(i18n('enter_full_name'))
    await call.answer()


# 2. Ismni qabul qilish va telefon so'rash
@dp.message(Register.full_name)
async def get_full_name(msg: types.Message, i18n: I18nContext, state: FSMContext):
    # Foydalanuvchi yuborgan ism xabarini o'chirib tashlaymiz (Chat toza turishi uchun)
    await msg.delete()

    await state.update_data(full_name=msg.text)
    await state.set_state(Register.phone_number)

    # ReplyKeyboard yuklanishi uchun yangi xabar yuboramiz
    await msg.answer(
        text=f"{i18n('enter_phone')}\n{i18n('regex_phone')}\n\n{i18n('use_phone_button')}",
        reply_markup=phone_number_request(i18n)
    )


# 3. Telefon raqamni qabul qilish va bazaga saqlash
@dp.message(Register.phone_number)
async def get_phone_number(msg: types.Message, i18n: I18nContext, state: FSMContext, db: AsyncSession):
    if msg.contact:
        phone = msg.contact.phone_number
    else:
        phone = msg.text

    if not is_valid_uz_phone(phone):
        # Noto'g'ri kiritilgan xabarni o'chirish
        await msg.delete()
        await msg.answer(i18n('invalid_phone_format'))
        return

    # Foydalanuvchi yuborgan telefon/kontakt xabarini o'chiramiz
    await msg.delete()

    await state.update_data(phone_number=phone)
    
    data = await state.get_data()
    full_name = data['full_name']
    language = data['language']
    phone_number = data['phone_number']

    try:
        # MUHIM: await qo'shildi!
        await create_user(
            session=db, 
            telegram_id=msg.from_user.id, 
            full_name=full_name, 
            phone_number=phone_number, 
            language=language
        )
        
        # Muvaffaqiyatli yakunlandi va Reply Keyboard olib tashlandi
        await msg.answer(
            f"{i18n('success_register')}", 
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.clear()
        
    except Exception as e:
        print(f"Error in registration: {e}")
        await msg.answer(i18n("error_server"))