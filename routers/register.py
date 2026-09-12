from aiogram import Router, types, F
from aiogram_i18n import I18nContext
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from states.register import Register
from buttons.keyboard.button import phone_number_request
from validation import is_valid_uz_phone
from crud.register import create_user
from buttons.inline.button import main_menu

dp = Router()


# 1. Til tanlash
@dp.callback_query(F.data.in_({"uz", "en", "ru"}))
async def change_language(call: types.CallbackQuery, i18n: I18nContext, state: FSMContext):
    lang = call.data
    await state.update_data(language=lang)
    await i18n.set_locale(lang)
    
    await state.set_state(Register.full_name)
    
    # Asosiy bot xabarining ID sini saqlab qo'yamiz (bitta xabarni tahrirlab borish uchun)
    await state.update_data(main_msg_id=call.message.message_id)
    
    await call.message.edit_text(i18n('enter_full_name'))
    await call.answer()


# 2. Ismni qabul qilish va telefon so'rash
@dp.message(Register.full_name)
async def get_full_name(msg: types.Message, i18n: I18nContext, state: FSMContext):
    data = await state.get_data()
    main_msg_id = data.get("main_msg_id")
    
    # User yuborgan ism xabarini o'chiramiz
    await msg.delete()

    await state.update_data(full_name=msg.text)
    await state.set_state(Register.phone_number)

    # Oldingi inline xabarni o'chirib, ReplyKeyboard bilan yangi xabar yuboramiz
    if main_msg_id:
        try:
            await msg.bot.delete_message(chat_id=msg.chat.id, message_id=main_msg_id)
        except Exception:
            pass

    sent_msg = await msg.answer(
        text=f"{i18n('enter_phone')}\n{i18n('regex_phone')}\n\n{i18n('use_phone_button')}",
        reply_markup=phone_number_request(i18n)
    )
    
    # Yangi xabar ID sini saqlaymiz
    await state.update_data(main_msg_id=sent_msg.message_id)


# 3. Telefon raqamni qabul qilish va bazaga saqlash
@dp.message(Register.phone_number)
async def get_phone_number(msg: types.Message, i18n: I18nContext, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    main_msg_id = data.get("main_msg_id")

    phone = msg.contact.phone_number if msg.contact else msg.text

    # User yuborgan telefon xabarini o'chiramiz
    await msg.delete()

    if not is_valid_uz_phone(phone):
        # Noto'g'ri raqam bo'lsa, asosiy xabar matnini xatolik haqida ogohlantirish bilan yangilaymiz
        if main_msg_id:
            await msg.bot.edit_message_text(
                chat_id=msg.chat.id,
                message_id=main_msg_id,
                text=f"{i18n('invalid_phone_format')}\n\n{i18n('enter_phone')}",
                reply_markup=phone_number_request(i18n)
            )
        return

    # Ishlov berish xabarini tozalash uchun eski promptni o'chiramiz
    if main_msg_id:
        try:
            await msg.bot.delete_message(chat_id=msg.chat.id, message_id=main_msg_id)
        except Exception:
            pass

    full_name = data['full_name']
    language = data['language']

    try:
        await create_user(
            session=db, 
            telegram_id=msg.from_user.id, 
            full_name=full_name, 
            phone_number=phone, 
            language=language
        )
        
        await state.clear()
        
        # Ro'yxatdan o'tish tugagach ReplyKeyboard yo'qolib, bitta asosiy menyu xabari chiqadi
        await msg.answer(
            text=f"{i18n('success_register')}\n\n{i18n('main')}\n{i18n('select_menu')}",
            reply_markup=main_menu(i18n=i18n)
        )
        
    except Exception as e:
        print(f"Error in registration: {e}")
        await msg.answer(i18n("error_server"))