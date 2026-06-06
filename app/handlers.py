import os
from ChatComplete.database import SessionLocal, User, BroadCast
from ChatComplete.generate import generate
from aiogram import F, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.enums import ContentType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, BufferedInputFile
from ChatComplete.config import TOKEN, ADMIN_ID
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime
import requests

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


# Клавиатура для оплаты Stars
payment = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оплатить ⭐', pay=True)]
])


def admin_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data='stats')],
        [InlineKeyboardButton(text='✉️ Рассылка', callback_data='broadcast')],
        [InlineKeyboardButton(text='⚙️ Доп настройки', callback_data='settings')]
    ])
    return keyboard

def mode_selection_keyboard():

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⚡ Быстрый ответ ', callback_data='mode_fast')],
        [InlineKeyboardButton(text='🐢 Углубленный ответ', callback_data='mode_deep')]
    ])
    return keyboard

def split_long_message(text: str, max_length: int = 4000) -> list:

    if len(text) <= max_length:
        return [text]

    parts = []
    lines = text.split('\n')
    current_part = ""

    for line in lines:
        if len(current_part) + len(line) + 1 <= max_length:
            if current_part:
                current_part += '\n'
            current_part += line
        else:
            if current_part:
                parts.append(current_part)
            if len(line) > max_length:
                for i in range(0, len(line), max_length):
                    parts.append(line[i:i + max_length])
                current_part = ""
            else:
                current_part = line

    if current_part:
        parts.append(current_part)

    return parts

def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🏠 Главное меню', callback_data='main_menu_call'),
         InlineKeyboardButton(text='🆕 Новое задание', callback_data='new_task')],
    ])
    return keyboard


def main_menu_settings():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⚙️ Настройки', callback_data='settings_data')],
        [InlineKeyboardButton(text='🏠 Главное меню', callback_data='main_menu_call'),
         InlineKeyboardButton(text='🆕 Новое задание', callback_data='new_task')]
    ])
    return keyboard


def main_menu_only():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🏠 Главное меню', callback_data='main_menu_call')]
    ])
    return keyboard


def profile_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔥 Профиль и бонусы', callback_data='profile')],
        [InlineKeyboardButton(text='🆕 Новое задание', callback_data='new_task')],
        [InlineKeyboardButton(text='✏️ Генерация изображения', callback_data='generate_picture')]
    ])
    return keyboard


def settings_reply():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⭐ Купить ответы', callback_data='buy_answer')],
        [InlineKeyboardButton(text='💎 Купить Premium (Stars)', callback_data='buy_premium')],
        [InlineKeyboardButton(text='🪙 Купить Premium (Crypto)', callback_data='buy_premium_crypto')],
        [InlineKeyboardButton(text='🏠 Главное меню', callback_data='main_menu_call')]
    ])
    return keyboard


def crypto_payment_menu():

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🪙 Оплатить (мин. $5)', url='https://t.me/send?start=IVqCfbALlVRJ')],
        [InlineKeyboardButton(text='✅ Я оплатил', callback_data='check_crypto_manual')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='settings_data')]
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
    await message.answer("Добро пожаловать в админ панель бота 🌍❤️!", reply_markup=admin_main_menu())


@router.callback_query(F.data == 'back')
async def back_menu(callback: CallbackQuery):
    await callback.message.answer("", reply_markup=admin_main_menu())
    await callback.answer()


@router.callback_query(F.data == 'stats')
async def stats_process(callback: CallbackQuery):
    db = SessionLocal()
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.active == True).count()
    db.close()
    text = f'📊 <b>Статистика:</b>\n\n├ Всего пользователей: {total_users}\n├ Активных: {active_users}\n└ Реферальная ссылка: t.me/reshebnik_Ai_do_Bot'
    await callback.message.answer(f'{text}', parse_mode='HTML')
    await callback.answer()


@router.callback_query(F.data == 'broadcast')
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст для рассылки ✉️")
    await state.set_state(BroadcastState.wait_text)
    await callback.answer()


@router.callback_query(F.data == 'settings')
async def settings(callback: CallbackQuery):
    await callback.message.answer("Здесь ничего нет пока!")
    await callback.answer()


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
    await message.answer(f"Рассылка завершена! Сообщение отправлено {count} пользователям.",
                         reply_markup=admin_main_menu())
    await state.clear()


@router.message(CommandStart())
async def start(message: Message):
    db = SessionLocal()
    existing = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()
    if not existing:
        new_user = User(telegram_id=message.from_user.id, name=message.from_user.full_name,
                        register_at=datetime.now().isoformat())
        db.add(new_user)
        db.commit()
    db.close()

    await message.answer(
        'Привет! 👋 Я — умный бот Решебник!\n\n<b>Что я умею:</b>\n✍️ Решаю задачи любой сложности\n📸 Понимаю фото из учебника\n💡 Пишу сочинения, рефераты и эссе\n🧮 Работаю с математическими формулами\n\nПогнали! Скидывай свое задание 🚀',
        parse_mode='HTML', reply_markup=profile_menu())


@router.message(Command('new'))
async def new_tasker_manager(message: Message):
    await message.answer(
        'Пришли задание:\n💬 напиши его текстом (рекомендуется)\n📸 или можешь отправить фото задания\n🗣 или отправь задание голосовым сообщением\n\n❗️Важно: один запрос = одно упражнение/задание',
        reply_markup=main_menu_only())


@router.message(Command('friend'))
async def friend_mod(message: Message):
    await message.answer(
        'Привет! 😊 Рад, что ты здесь! Можешь рассказывать мне о чем угодно — о своих увлечениях, мечтах, переживаниях или просто делиться классными моментами из жизни. Я всегда поддержу, подбодрю или просто посмеюсь вместе с тобой. Го общаться!')


@router.message(Command('settings'))
async def settings_command(message: Message):
    await message.answer(
        '<b>⚙️ Настройки</b>\n\nТариф: 🆓 Free\n\n🌎 Язык ответов: 🇷🇺 Russian',
        parse_mode='HTML', reply_markup=settings_reply())


@router.message(Command('privacy', 'terms'))
async def privacy(message: Message):
    await message.answer(
        '<b>Политика конфиденциальности</b>\n\n<b>1. Введение</b>\n\nЭта Политика конфиденциальности описывает, как мы используем и защищаем ваши данные.\n\n<b>2. Данные, которые мы собираем</b>\n\nКогда вы взаимодействуете с нашим ботом, мы собираем основную информацию о вашем профиле.\n\n<b>3. Правовые основания для обработки персональных данных</b>\n\nМы используем ваши данные для обеспечения функционирования бота и технической поддержки.\n\n<b>4. Раскрытие персональных данных</b>\n\nМы не передаем ваши данные третьим лицам.\n\n<b>5. Удаление персональных данных</b>\n\nВы можете удалить свои данные, заблокировав бота.\n\n<b>6. Изменения в Политике конфиденциальности</b>\n\nЭта Политика может измениться в любое время.',
        parse_mode='HTML', reply_markup=main_menu())


@router.message(Command('reshebnik'))
async def reshebnik_mod(message: Message):
    await message.answer(
        'Пришли задание:\n💬 напиши его текстом (рекомендуется)\n📸 или можешь отправить фото задания\n🗣 или отправь задание голосовым сообщением\n\n❗️Важно: один запрос = одно упражнение/задание',
        reply_markup=main_menu_only())


# ========== ОПЛАТА TELEGRAM STARS ==========
@router.callback_query(F.data == 'buy_answer')
async def buy_answers(callback: CallbackQuery):
    prices = [LabeledPrice(label="XTR", amount=50)]
    await callback.message.answer_invoice(
        title='⭐ Покупка ответов',
        description='Купить дополнительные ответы для бота',
        prices=prices,
        provider_token='',
        payload='buy_answers',
        currency='XTR',
        reply_markup=payment,
    )


@router.callback_query(F.data == 'buy_premium')
async def buy_premium_stars(callback: CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()

    if user and user.premium:
        await callback.answer('❌ У вас уже есть Premium подписка!', show_alert=True)
        db.close()
        return

    db.close()
    await callback.answer()

    prices = [LabeledPrice(label="XTR", amount=250)]
    await callback.message.answer_invoice(
        title='💎 Premium подписка (навсегда)',
        description='• Генерация изображений\n• Распознавание текста с фото\n• Приоритетная поддержка\n• Premium НАВСЕГДА!',
        prices=prices,
        provider_token='',
        payload='premium_subscription',
        currency='XTR',
        reply_markup=payment,
    )


# ========== ОПЛАТА CRYPTO BOT ==========
@router.callback_query(F.data == 'buy_premium_crypto')
async def buy_premium_crypto(callback: CallbackQuery):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()

    if user and user.premium:
        await callback.answer('❌ У вас уже есть Premium подписка!', show_alert=True)
        db.close()
        return

    db.close()
    await callback.answer()

    await callback.message.answer(
        '🪙 **Оплата Premium подписки через Crypto Bot**\n\n'
        '💰 **Минимальная сумма: $5**\n'
        '💎 Premium активируется НАВСЕГДА после оплаты\n\n'
        '📌 **Инструкция:**\n'
        '1️⃣ Нажмите кнопку "Оплатить (мин. $5)"\n'
        '2️⃣ Выберите удобную валюту (USDT, BTC, TON, TRX, DOGE, SOL, ETH)\n'
        '3️⃣ Оплатите любую сумму от $5\n'
        '4️⃣ После оплаты нажмите "✅ Я оплатил"\n\n'
        '🔗 **Ссылка для оплаты:**\n'
        '`https://t.me/send?start=IVqCfbALlVRJ`',
        parse_mode='Markdown',
        reply_markup=crypto_payment_menu()
    )


@router.callback_query(F.data == 'check_crypto_manual')
async def check_crypto_manual(callback: CallbackQuery):
    """Пользователь нажал 'Я оплатил'"""

    await callback.message.answer(
        '✅ **Ваша заявка принята!**\n\n'
        '🔍 Администратор проверит платеж в ближайшее время.\n'
        '⏱ Обычно это занимает до 24 часов.\n\n'
        '📌 После подтверждения Premium будет активирован навсегда!',
        parse_mode='Markdown'
    )

    # Уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f'🆕 **Новая заявка на Premium!**\n\n'
        f'👤 Пользователь: {callback.from_user.full_name}\n'
        f'🆔 ID: {callback.from_user.id}\n'
        f'💰 Сумма: от $5\n\n'
        f'✅ После проверки оплаты выполните:\n'
        f'`/activate_premium {callback.from_user.id}`',
        parse_mode='Markdown'
    )

    await callback.answer('Заявка отправлена администратору!')


# ========== КОМАНДА ДЛЯ АДМИНА ==========
@router.message(Command('activate_premium'))
async def activate_premium_admin(message: Message):
    """Активация Premium администратором вручную"""
    if message.from_user.id != ADMIN_ID:
        await message.answer('❌ У вас нет доступа!')
        return

    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer('❌ Использование: /activate_premium <telegram_id>')
            return

        user_id = args[1]

        db = SessionLocal()
        user = db.query(User).filter(User.telegram_id == user_id).first()

        if user:
            user.premium = True
            db.commit()

            await message.answer(f'✅ Premium активирован для {user.name} (ID: {user_id})')

            # Отправляем уведомление пользователю
            try:
                await bot.send_message(
                    int(user_id),
                    '✅ **Premium подписка активирована!** 🎉\n\n'
                    '🎨 Теперь вам доступна генерация изображений!\n'
                    '💎 Premium НАВСЕГДА!\n\n'
                    'Спасибо за покупку! 🙏',
                    parse_mode='Markdown'
                )
            except Exception as e:
                await message.answer(f'⚠️ Не удалось уведомить пользователя: {e}')
        else:
            await message.answer(f'❌ Пользователь с ID {user_id} не найден')

        db.close()

    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')


# ========== ОБРАБОТЧИКИ ПЛАТЕЖЕЙ STARS ==========
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payments_data = message.successful_payment
    payload = payments_data.invoice_payload
    user_id = str(message.from_user.id)

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()

    if not user:
        user = User(telegram_id=user_id, name=message.from_user.full_name, register_at=datetime.now().isoformat())
        db.add(user)
        db.commit()

    if payload == 'premium_subscription':
        user.premium = True
        db.commit()
        await message.answer(
            f"✅ **Premium подписка активирована НАВСЕГДА!**\n\n"
            f"⭐ Оплачено: {payments_data.total_amount // 100} звёзд\n\n"
            f"🎨 Теперь вам доступна генерация изображений!",
            parse_mode='Markdown',
            message_effect_id="5104841245755180586"
        )
    elif payload == 'buy_answers':
        await message.answer(
            f"✅ **Оплата прошла успешно!**\n\n"
            f"⭐ Получено: {payments_data.total_amount // 100} звёзд\n"
            f"📚 Вам начислены дополнительные ответы!",
            parse_mode='Markdown',
            message_effect_id="5104841245755180586"
        )

    db.close()


@router.callback_query(F.data == 'settings_data')
async def setting_data_get(callback: CallbackQuery):
    await callback.message.answer(
        '<b>⚙️ Настройки</b>\n\nТариф: 🆓 Free\n\n🌎 Язык ответов: 🇷🇺 Russian',
        parse_mode='HTML', reply_markup=settings_reply())


# ========== ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ (ТОЛЬКО ДЛЯ PREMIUM) ==========
@router.callback_query(F.data == 'generate_picture')
async def generate_pictures(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()
    premium_by_user = user.premium if user else False
    db.close()

    if premium_by_user is True or callback.from_user.id == ADMIN_ID:
        await state.set_state(Generate.prompt)
        await callback.message.answer('🎨 Введите текст для генерации изображения (промпт)')
        await callback.answer()
    else:
        await callback.message.answer(
            '❌ У вас нет Premium подписки!\n\n'
            '💎 Чтобы пользоваться генерацией изображений, приобретите Premium в меню настроек'
        )
        await callback.answer()


@router.message(Generate.prompt)
async def generating_picture(message: Message, state: FSMContext):
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
    await callback.answer()
    await callback.message.answer(
        'Привет! 👋 Я — умный бот Решебник!\n\n<b>Что я умею:</b>\n✍️ Решаю задачи любой сложности\n📸 Понимаю фото из учебника\n💡 Пишу сочинения, рефераты и эссе\n🧮 Работаю с математическими формулами\n\nПогнали! Скидывай свое задание 🚀',
        parse_mode='HTML', reply_markup=profile_menu())


@router.callback_query(F.data == 'new_task')
async def new_task(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        'Пришли задание:\n💬 напиши его текстом (рекомендуется)\n📸 или можешь отправить фото задания\n🗣 или отправь задание голосовым сообщением\n\n❗️Важно: один запрос = одно упражнение/задание',
        reply_markup=main_menu_only())


@router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery):
    await callback.answer()
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()
    premium_status = '✅ Да (навсегда)' if user and user.premium else '❌ Нет'
    register_at = user.register_at if user else 'Неизвестно'
    db.close()

    text_bot = f'ℹ️ <b>Ваш профиль</b>\n\n'
    text_bot += f'🏷️ <b>Имя:</b> {callback.from_user.full_name}\n'
    text_bot += f'🔗 <b>Username:</b> @{callback.from_user.username}\n'
    text_bot += f'📆 <b>Регистрация:</b> {register_at}\n'
    text_bot += f'💎 <b>Premium подписка:</b> {premium_status}\n\n'
    text_bot += f'<i>💎 Premium дает доступ к генерации изображений</i>'

    await callback.message.answer(f'{text_bot}', parse_mode='HTML', reply_markup=main_menu_settings())


# ========== ОБРАБОТКА ТЕКСТОВЫХ ЗАДАНИЙ ==========
@router.message(F.text)
async def text_ai(message: Message, state: FSMContext):
    text = message.text.strip()

    if len(text) < 3:
        await message.answer('❌ Пожалуйста, напишите более подробное задание или вопрос.')
        return

    # Сохраняем текст в состояние
    await state.update_data(user_text=text)

    # Спрашиваем режим ответа
    await message.answer(
        f'📝 **Ваш запрос:**\n`{text[:150]}...`\n\n🤔 **Выберите режим ответа:**',
        parse_mode='Markdown',
        reply_markup=mode_selection_keyboard()
    )


# ========== ВЫБОР РЕЖИМА ОТВЕТА ==========
@router.callback_query(F.data.startswith('mode_'))
async def process_mode_selection(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.replace('mode_', '')  # 'fast' или 'deep'

    # Получаем сохраненные данные
    data = await state.get_data()

    # Определяем тип запроса
    if 'recognized_text' in data:
        user_input = data['recognized_text']
        text_to_ai = f'Помоги решить задание. Вот текст с фото: {user_input}'
        input_type = "фото"
    else:
        user_input = data.get('user_text', '')
        text_to_ai = f'Помоги решить задание: {user_input}'
        input_type = "текст"

    if not user_input:
        await callback.message.answer('❌ Ошибка: данные не найдены. Отправьте задание заново.')
        await state.clear()
        await callback.answer()
        return

    # Режим ответа
    is_fast = (mode == "fast")
    mode_text = "⚡ БЫСТРЫЙ" if is_fast else "🐢 УГЛУБЛЕННЫЙ"

    # Отправляем сообщение о начале генерации
    think_message = await callback.message.answer(f'🤖 Думаю... (режим: {mode_text})')

    # Генерируем ответ
    response_txt = await generate(text_to_ai, fast=is_fast)

    # Отправляем ответ
    if len(response_txt) > 4000:
        await think_message.delete()
        parts = split_long_message(response_txt)

        await callback.message.answer(
            f'✅ **Ответ готов!** (режим: {mode_text})\n\n{parts[0]}',
            parse_mode='Markdown'
        )
        for part in parts[1:]:
            await callback.message.answer(part, parse_mode='Markdown')
        await callback.message.answer(
            '<b>Задавай вопросы 😄 еще!</b>',
            parse_mode='HTML'
        )
    else:
        await think_message.edit_text(
            f'✅ **Ответ готов!** (режим: {mode_text})\n\n{response_txt}\n\n<b>Задавай вопросы 😄 еще!</b>',
            parse_mode='HTML'
        )

    # Очищаем состояние
    await state.clear()
    try:
        await callback.answer()
    except:
        pass
