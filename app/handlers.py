import os
from database import SessionLocal, User, BroadCast
from generate import generate
from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.enums import ContentType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, BufferedInputFile
from config import TOKEN, ADMIN_ID
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime
import requests
from PIL import Image
import io

# API ключ для OCR.space
OCR_API_KEY = "K86426589588957"

bot = Bot(token=TOKEN)
Currency = 'XTR'
ADMIN_ID = ADMIN_ID

router = Router()


class Generate(StatesGroup):
    prompt = State()


class BroadcastState(StatesGroup):
    wait_text = State()


payment = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оплатить ⭐', pay=True)]
])


def admin_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊‍ Статистика", callback_data='stats')],
        [InlineKeyboardButton(text='✉️ Рассылка', callback_data='broadcast')],
        [InlineKeyboardButton(text='⚙️ Доп настройки', callback_data='settings')]
    ])
    return keyboard


def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🏠Главное меню', callback_data='main_menu_call'),
         InlineKeyboardButton(text='🆕Новое задание', callback_data='new_task')],
    ])
    return keyboard


def main_menu_settings():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⚙️ Настройки', callback_data='settings_data')],
        [InlineKeyboardButton(text='🏠Главное меню', callback_data='main_menu_call'),
         InlineKeyboardButton(text='🆕Новое задание', callback_data='new_task')]
    ])
    return keyboard


def main_menu_only():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🏠Главное меню', callback_data='main_menu_call')]
    ])
    return keyboard


def profile_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔥Профиль и бонусы', callback_data='profile')],
        [InlineKeyboardButton(text='🆕Новое задание', callback_data='new_task')],
        [InlineKeyboardButton(text='✏️ Генерация изображения', callback_data='generate_picture')]
    ])
    return keyboard


def settings_reply():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⚡ Купить ответы', callback_data='buy_answer'),
         InlineKeyboardButton(text='💎 Купить Premium', callback_data='buy_premium')],
        [InlineKeyboardButton(text='🏠Главное меню', callback_data='main_menu_call')]
    ])
    return keyboard


async def ocr_space_file(file_path: str):
    """Распознавание текста через OCR.space API"""
    with open(file_path, 'rb') as f:
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': f},
            data={
                'apikey': OCR_API_KEY,
                'language': 'rus',
                'isOverlayRequired': False,
                'filetype': 'PNG',
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2
            },
            timeout=30
        )

    result = response.json()

    if result.get('IsErroredOnProcessing'):
        error_msg = result.get('ErrorMessage', ['Unknown error'])[0]
        raise Exception(f"OCR Error: {error_msg}")

    parsed_text = result.get('ParsedResults', [{}])[0].get('ParsedText', '')
    parsed_text = parsed_text.strip()

    if not parsed_text:
        raise Exception("Текст не найден на изображении")

    return parsed_text


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('У вас нет доступа к этой команде.')
        return
    await message.answer("Добро пожаловать в админ панель бота 🌍❤️❤️!", reply_markup=admin_main_menu())


@router.callback_query(F.data == 'back')
async def back_menu(callback: CallbackQuery):
    await callback.message.answer("", reply_markup=admin_main_menu())
    await callback.answer('')


@router.callback_query(F.data == 'stats')
async def stats_process(callback: CallbackQuery):
    db = SessionLocal()
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.active == True).count()
    db.close()
    text = f'📊 <b>Статистика:</b>\n\n├ Всего 👀 пользователей: {total_users}\n├ Активных 🎮 пользователей : {active_users}\n└ Реферальная ссылка 📎 : t.me/reshebnik_Ai_do_Bot'
    await callback.message.answer(f'{text}', parse_mode='HTML')
    await callback.answer('')


@router.callback_query(F.data == 'broadcast')
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст для рассылки ✉️")
    await state.set_state(BroadcastState.wait_text)
    await callback.answer('')


@router.callback_query(F.data == 'settings')
async def settings(callback: CallbackQuery):
    await callback.message.answer("Здесь ничего нет пока!")
    await callback.answer('')


@router.message(BroadcastState.wait_text)
async def broadcast_mess(message: Message, state: FSMContext, bot: Bot):
    broadcast_text = message.text
    db = SessionLocal()
    users_list = db.query(User).filter(User.active == True).all()
    count = 0
    for user in users_list:
        try:
            await bot.send_message(user.telegram_id, broadcast_text)
            count += 1
        except Exception as e:
            print(f'Failed to send to {user.telegram_id}:{e}')
    new_broadcast = BroadCast(message=broadcast_text)
    db.add(new_broadcast)
    db.commit()
    db.close()
    await message.answer(f"Рассылка завершена ✉️ ! Сообщение отправлено {count} пользователям 🕵️.",
                         reply_markup=admin_main_menu())
    await state.clear()


@router.message(CommandStart())
async def start(message: Message):
    db = SessionLocal()
    exiting = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if not exiting:
        new_user = User(telegram_id=message.from_user.id, name=message.from_user.full_name,
                        register_at=datetime.now().isoformat())
        db.add(new_user)
        db.commit()
    db.close()

    await message.answer(
        'Привет! 👋 Я — умный бот Решебник!\n\n<b>Что я умею:</b>\n✍️ Решаю задачи любой сложности\n📸 Понимаю фото из учебника и голосовые сообщения              \n💡 Пишу сочинения, рефераты и эссе\n🧮 Работаю с математическими формулами\n\n<b>Лайфхаки для лучшего результата:</b>\n• Делай четкие фото при хорошем свете\n• Выбери нужный язык в настройках\n• Уточняй номер задания на фото\n• Пиши после ответа доп.вопросы, если нужно больше\nинформации\n• Жми "Новое задание" для следующей задачи\n\nПогнали! Скидывай свое задание 🚀',
        parse_mode='HTML', reply_markup=profile_menu())


@router.message(Command('new'))
async def new_tasker_manager(message: Message):
    await message.answer(
        'Пришли задание:\n💬 напиши его текстом (рекомендуется)\n📸 или можешь отправить фото задания прямо из учебника /\nтетради\n🗣 или отправь задание голосовым сообщением\n\n❗️Важно: один запрос = одно упражнение/задание',
        reply_markup=main_menu_only())


@router.message(Command('friend'))
async def friend_mod(message: Message):
    await message.answer(
        'Привет! 😊 Рад, что ты здесь! Можешь рассказывать мне о чем \nугодно — о своих увлечениях, мечтах, переживаниях или \nпросто делиться классными моментами из жизни. Я всегда\nподдержу, подбодрю или просто посмеюсь вместе с тобой. Го\nобщаться!')


@router.message(Command('settings'))
async def settings(message: Message):
    await message.answer(
        '<b>⚙️ Настройки</b>\n\nТариф: 🆓 Free\n\nОтветы: ⚡️ 3\n\n🆓 Ответы за друзей: 💰 0 USD₮\n\n🌎 Язык ответов: 🇷🇺 Russian',
        parse_mode='HTML', reply_markup=settings_reply())


@router.message(Command('privacy', 'terms'))
async def privacy(message: Message):
    await message.answer(
        '<b>Политика конфиденциальности</b>\n\n<b>1. Введение</b>\n\nЭта Политика конфиденциальности описывает, как мы,\nвладельцы бота используем и защищаем ваши данные. Эти \nданные могут быть предоставлены вами или получены нами \nпри взаимодействии с ботом. В этой Политике \nпри взаимодействии с ботом. В этой Политике\nконфиденциальности "мы", "нас" и "наш" относятся к \nвладельцам бота, а "вы" — к пользователю.\nЭтот бот является частью экосистемы ботов Telegram. Чтобы\nузнать больше об услугах обмена сообщениями Telegram, \nознакомьтесь с <a href="https://telegram.org/privacy/?setln=ru">Политикой конфиденциальности Telegram</a> .\n\n<b>2. Данные, которые мы собираем</b>\n\nКогда вы взаимодействуете с нашим ботом, мы собираем \nосновную информацию о вашем профиле, такую как ваше имя,\nфамилия, имя пользователя и изображение профиля, как это\nпредусмотрено Telegram. Эти данные хранятся бессрочно. Мы\nтакже сохраняем все сообщения, которые вы отправляете \nнашему боту, пока он остается активным — эти сообщения\nмогут содержать персональные данные.\n\n<b>3. Правовые основания для обработки персональных данных</b>\n\nМы используем ваши данные для:\n1. Обеспечение надлежащего функционирования нашего чат-\nбота.\n2. Предоставление технической поддержки — например, мы\nможем использовать имя пользователя в Telegram, чтобы\nбыстро найти ваш чат.\n3. Вычисление статистики использования бота.\n\n<b>4. Раскрытие персональных данных</b>\n\nДля предоставления услуг мы используем сторонние \nинструменты для обработки данных. Например, третьи стороны \nданные пользователей третьим лицам за исключением случаев, \nкогда этого требует законодательство или запросы органов \nвласти. Ваши данные хранятся в пределах Европейского Союза\nи могут быть переданы только в страны, которые соответствуют \nстандартам защиты, установленным Европейской Комиссией.\n\n<b>5. Удаление персональных данных</b>\n\nВы можете удалить свои данные, заблокировав наш Telegram-\nбот — это запустит автоматическое удаление данных.\nНекоторые данные могут храниться до 30 дней.\n\n<b>6. Изменения в Политике конфиденциальности</b>\n\nЭта Политика конфиденциальности может измениться в любое \nвремя. Чтобы просмотреть нашу текущую Политику \nконфиденциальности, отправьте команду /privacy.',
        parse_mode='HTML', reply_markup=main_menu())


@router.message(Command('reshebnik'))
async def reshebnik_mod(message: Message):
    await message.answer(
        'Пришли задание:\n💬 напиши его текстом (рекомендуется)\n📸 или можешь отправить фото задания прямо из учебника /\nтетради\n🗣 или отправь задание голосовым сообщением\n\n❗️Важно: один запрос = одно упражнение/задание',
        reply_markup=main_menu_only())


@router.callback_query(F.data == 'buy_answer')
async def money_key(callback: CallbackQuery):
    prices = [LabeledPrice(label=Currency, amount=50)]
    await callback.message.answer_invoice(
        title='Поддержка бота 💰',
        description='Купить ответы для бота Reshebnik',
        prices=prices,
        provider_token='',
        payload='channel_support',
        currency=Currency,
        reply_markup=payment,
    )


@router.pre_checkout_query()
async def prechekout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    await message.answer(f'{message.successful_payment.telegram_payment_charge_id}',
                         message_effect_id="5104841245755180586")


@router.callback_query(F.data == 'buy_premium')
async def buy_premium_callback(callback: CallbackQuery):
    prices = [LabeledPrice(label=Currency, amount=250)]
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()
    if user and user.premium is True:
        await callback.message.answer('У вас уже есть подписка 💎Premium')
        db.close()
        return
    db.close()

    await callback.message.answer_invoice(
        title='Покупка 💎Premium для бота',
        description='Купить Premium для бота Reshebnik',
        prices=prices,
        provider_token='',
        payload='premium_purchase',
        currency=Currency,
        reply_markup=payment,
    )


@router.pre_checkout_query()
async def prechekout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()
    if user:
        user.premium = True
        db.commit()
        await message.answer(
            f'✅ Поздравляем! Вы приобрели Premium подписку!\n'
            f'ID оплаты: {message.successful_payment.telegram_payment_charge_id}',
            message_effect_id="5104841245755180586"
        )
    db.close()


@router.callback_query(F.data == 'settings_data')
async def setting_data_get(callback: CallbackQuery):
    await callback.message.answer(
        '<b>⚙️ Настройки</b>\n\nТариф: 🆓 Free\n\nОтветы: ⚡️ 3\n\n🆓 Ответы за друзей: 💰 0 USD₮\n\n🌎 Язык ответов: 🇷🇺 Russian',
        parse_mode='HTML', reply_markup=settings_reply())


# ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ (ТОЛЬКО ДЛЯ PREMIUM)
@router.callback_query(F.data == 'generate_picture')
async def generate_pictures(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()
    premium_by_user = user.premium if user else False
    db.close()

    # Проверка на Premium или админа
    if premium_by_user is True or callback.from_user.id == ADMIN_ID:
        await state.set_state(Generate.prompt)
        await callback.message.answer('🎨 Введите текст для генерации изображения (промпт)')
        await callback.answer('')
    else:
        await callback.message.answer(
            '❌ У вас нет Premium подписки!\n\n'
            '💎 Чтобы пользоваться генерацией изображений, приобретите Premium:\n'
            '👉 Нажмите "💎 Купить Premium" в меню настроек'
        )
        await callback.answer('')
        await state.clear()


@router.message(Generate.prompt)
async def generating_picture(message: Message, state: FSMContext):
    # Дополнительная проверка Premium на случай прямого ввода
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()
    premium_by_user = user.premium if user else False
    db.close()

    if premium_by_user is False and message.from_user.id != ADMIN_ID:
        await message.answer('❌ У вас нет Premium подписки для генерации изображений!')
        await state.clear()
        return

    prompt = message.text.strip()
    thinking_msg = await message.answer("🎨 Генерирую изображение... Подождите немного")

    try:
        # Генерация изображения через Pollinations.ai (бесплатно)
        img_url = f"https://image.pollinations.ai/prompt/{prompt}?width=1024&height=1024"
        img_response = requests.get(img_url, timeout=60)

        if img_response.status_code == 200:
            await message.answer_photo(
                BufferedInputFile(img_response.content, "image.png"),
                caption=f'<b>Ваш промпт:</b> {prompt}\n\n✅ Изображение сгенерировано!\n💎 Premium функция',
                parse_mode='HTML',
                reply_markup=main_menu_settings()
            )
            await thinking_msg.delete()
        else:
            await thinking_msg.edit_text("❌ Не удалось сгенерировать изображение. Попробуйте другой промпт.")

    except Exception as e:
        print(f"Ошибка генерации: {e}")
        await thinking_msg.edit_text("❌ Ошибка генерации. Попробуйте позже.")

    await state.clear()


@router.callback_query(F.data == 'main_menu_call')
async def main_menu_call(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.answer(
        'Привет! 👋 Я — умный бот Решебник!\n\n<b>Что я умею:</b>\n✍️ Решаю задачи любой сложности\n📸 Понимаю фото из учебника и голосовые сообщения              \n💡 Пишу сочинения, рефераты и эссе\n🧮 Работаю с математическими формулами\n\n<b>Лайфхаки для лучшего результата:</b>\n• Делай четкие фото при хорошем свете\n• Выбери нужный язык в настройках\n• Уточняй номер задания на фото\n• Пиши после ответа доп.вопросы, если нужно больше\nинформации\n• Жми "Новое задание" для следующей задачи\n\nПогнали! Скидывай свое задание 🚀',
        parse_mode='HTML', reply_markup=profile_menu())


@router.callback_query(F.data == 'new_task')
async def new_task(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.answer(
        'Пришли задание:\n💬 напиши его текстом (рекомендуется)\n📸 или можешь отправить фото задания прямо из учебника /\nтетради\n🗣 или отправь задание голосовым сообщением\n\n❗️Важно: один запрос = одно упражнение/задание',
        reply_markup=main_menu_only())


@router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery):
    await callback.answer('')
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()
    if user:
        premium_by_us = '✅ Да' if user.premium else '❌ Нет'
        user_register_at = user.register_at
    else:
        premium_by_us = '❌ Нет'
        user_register_at = 'Неизвестно'
    db.close()

    text_bot = f'ℹ️ <b>Ваш профиль</b>\n\n'
    text_bot += f'🏷️ <b>Имя:</b> {callback.from_user.full_name}\n'
    text_bot += f'🔗 <b>Username:</b> @{callback.from_user.username}\n'
    text_bot += f'🆔 <b>ID:</b> {callback.from_user.id}\n'
    text_bot += f'📆 <b>Регистрация:</b> {user_register_at}\n'
    text_bot += f'💎 <b>Premium подписка:</b> {premium_by_us}\n'
    text_bot += f'🗣️ <b>Язык:</b> {callback.from_user.language_code}\n\n'
    text_bot += f'<i>💎 Premium дает доступ к генерации изображений</i>'

    await callback.message.answer(f'{text_bot}', parse_mode='HTML', reply_markup=main_menu_settings())


# ОБРАБОТКА ФОТО С ЗАДАНИЯМИ (ДОСТУПНО ВСЕМ)
@router.message(F.content_type == ContentType.PHOTO)
async def photo_answer(message: Message):
    think_message = await message.answer('🤖 Распознаю текст и думаю...')

    # Скачиваем фото
    photo_id = message.photo[-1].file_id
    photo_file = await bot.get_file(photo_id)
    file_path = f"temp_{photo_id}.png"
    await bot.download_file(photo_file.file_path, file_path)

    try:
        # Распознаем текст через OCR.space
        recognized_text = await ocr_space_file(file_path)

        # Если текст не распознан
        if not recognized_text or len(recognized_text) < 2:
            await think_message.edit_text(
                '❌ Не удалось распознать текст на изображении.\n\nПопробуйте:\n• Сделать фото более четким\n• Отправить задание текстом\n• Использовать лучшее освещение')
            os.remove(file_path)
            return

        # Отправляем в AI (доступно всем)
        text_to_ai = f'Помоги решить задание. Вот текст с фото: {recognized_text}'
        response_txt = await generate(text_to_ai)

        await think_message.edit_text(
            f'✅ <b>Ответ готов!</b>\n\n{response_txt}\n\n<b>Задавай вопросы 😄 еще!</b>',
            parse_mode='HTML')

    except Exception as e:
        print(f"OCR Error: {e}")
        await think_message.edit_text(
            '❌ Произошла ошибка при распознавании текста.\n\nПопробуйте:\n• Отправить задание текстом\n• Сделать фото более качественным')
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ОБРАБОТКА ТЕКСТОВЫХ ЗАДАНИЙ (ДОСТУПНО ВСЕМ)
@router.message(F.text)
async def text_ai(message: Message):
    think_message = await message.answer('🤖 Думаю...')
    text = message.text.strip()

    if len(text) < 3:
        await think_message.edit_text('❌ Пожалуйста, напишите более подробное задание или вопрос.')
        return

    text_to_ai = f'Помоги решить задание: {text}'
    response_txt = await generate(text_to_ai)

    await think_message.edit_text(
        f'✅ <b>Ответ готов!</b>\n\n{response_txt}\n\n<b>Задавай вопросы 😄 еще!</b>',
        parse_mode='HTML')
