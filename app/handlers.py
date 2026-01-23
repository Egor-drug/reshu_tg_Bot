import os
from ChatComplete.database import SessionLocal, User, BroadCast
from ChatComplete.generate import generate
from aiogram import F, Router,Bot
from aiogram.filters import CommandStart,Command
from aiogram.enums import ContentType
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.types import Message,CallbackQuery,LabeledPrice,PreCheckoutQuery,BufferedInputFile
from ChatComplete.config import TOKEN,ADMIN_ID
import easyocr

from aiogram.fsm.state import State,StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime
import requests

from PIL import Image


bot = Bot(token=TOKEN)



Currency = 'XTR'
ADMIN_ID = ADMIN_ID

OPENROUTER_API_KEY = "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"

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
        [InlineKeyboardButton(text='🏠Главное меню',callback_data='main_menu_call'),InlineKeyboardButton(text='🆕Новое задание',callback_data='new_task')],

    ])
    return keyboard
def main_menu_settings():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⚙️ Настройки',callback_data='settings_data')],
        [InlineKeyboardButton(text='🏠Главное меню',callback_data='main_menu_call'),InlineKeyboardButton(text='🆕Новое задание',callback_data='new_task')]
    ])
    return keyboard


def main_menu_only():
  keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🏠Главное меню', callback_data='main_menu_call')]

  ])
  return keyboard
def profile_menu():
   keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔥Профиль и бонусы',callback_data='profile')],
        [InlineKeyboardButton(text='🆕Новое задание',callback_data='new_task')],
       [InlineKeyboardButton(text='✏️ Генерация изображения', callback_data='generate_picture')]
   ])
   return keyboard
def settings_reply():
  keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⚡ Купить ответы', callback_data='buy_answer'),InlineKeyboardButton(text='💎 Купить Premium',callback_data='buy_premium')],
    [InlineKeyboardButton(text='🏠Главное меню', callback_data='main_menu_call')]
  ])
  return keyboard






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
    await callback.message.answer(f'{text}',parse_mode='HTML')
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
async def start(message:Message):
     db = SessionLocal()
     exiting = db.query(User).filter(User.telegram_id == message.from_user.id).first()
     if not exiting:
         new_user = User(telegram_id=message.from_user.id, name=message.from_user.full_name,register_at=datetime.now().isoformat())
         db.add(new_user)

         db.commit()
     db.close()

     await message.answer('Привет! 👋 Я — умный бот Решебник!\n\n<b>Что я умею:</b>\n✍️ Решаю задачи любой сложности\n📸 Понимаю фото из учебника и голосовые сообщения              \n💡 Пишу сочинения, рефераты и эссе\n🧮 Работаю с математическими формулами\n\n<b>Лайфхаки для лучшего результата:</b>\n• Делай четкие фото при хорошем свете\n• Выбери нужный язык в настройках\n• Уточняй номер задания на фото\n• Пиши после ответа доп.вопросы, если нужно больше\nинформации\n• Жми "Новое задание" для следующей задачи\n\nПогнали! Скидывай свое задание 🚀',parse_mode='HTML',reply_markup=profile_menu())







@router.message(Command('new'))
async def new_tasker_manager(message:Message):

  await message.answer('Пришли задание:\n💬 напиши его текстом (рекомендуется)\n📸 или можешь отправить фото задания прямо из учебника /\nтетради\n🗣 или отправь задание голосовым сообщением\n\n❗️Важно: один запрос = одно упражнение/задание',reply_markup=main_menu_only())



@router.message(Command('friend'))
async def friend_mod(message:Message):
  await message.answer('Привет! 😊 Рад, что ты здесь! Можешь рассказывать мне о чем \nугодно — о своих увлечениях, мечтах, переживаниях или \nпросто делиться классными моментами из жизни. Я всегда\nподдержу, подбодрю или просто посмеюсь вместе с тобой. Го\nобщаться!')




@router.message(Command('settings'))
async def settings(message:Message):
  await message.answer('<b>⚙️ Настройки</b>\n\nТариф: 🆓 Free\n\nОтветы: ⚡️ 3\n\n🆓 Ответы за друзей: 💰 0 USD₮\n\n🌎 Язык ответов: 🇷🇺 Russian',parse_mode='HTML',reply_markup=settings_reply())



@router.message(Command('privacy','terms'))
async def privacy(message:Message):
  await message.answer('<b>Политика конфиденциальности</b>\n\n<b>1. Введение</b>\n\nЭта Политика конфиденциальности описывает, как мы,\nвладельцы бота используем и защищаем ваши данные. Эти \nданные могут быть предоставлены вами или получены нами \nпри взаимодействии с ботом. В этой Политике \nпри взаимодействии с ботом. В этой Политике\nконфиденциальности "мы", "нас" и "наш" относятся к \nвладельцам бота, а "вы" — к пользователю.\nЭтот бот является частью экосистемы ботов Telegram. Чтобы\nузнать больше об услугах обмена сообщениями Telegram, \nознакомьтесь с <a href="https://telegram.org/privacy/?setln=ru">Политикой конфиденциальности Telegram</a> .\n\n<b>2. Данные, которые мы собираем</b>\n\nКогда вы взаимодействуете с нашим ботом, мы собираем \nосновную информацию о вашем профиле, такую как ваше имя,\nфамилия, имя пользователя и изображение профиля, как это\nпредусмотрено Telegram. Эти данные хранятся бессрочно. Мы\nтакже сохраняем все сообщения, которые вы отправляете \nнашему боту, пока он остается активным — эти сообщения\nмогут содержать персональные данные.\n\n<b>3. Правовые основания для обработки персональных данных</b>\n\nМы используем ваши данные для:\n1. Обеспечение надлежащего функционирования нашего чат-\nбота.\n2. Предоставление технической поддержки — например, мы\nможем использовать имя пользователя в Telegram, чтобы\nбыстро найти ваш чат.\n3. Вычисление статистики использования бота.\n\n<b>4. Раскрытие персональных данных</b>\n\nДля предоставления услуг мы используем сторонние \nинструменты для обработки данных. Например, третьи стороны \nданные пользователей третьим лицам за исключением случаев, \nкогда этого требует законодательство или запросы органов \nвласти. Ваши данные хранятся в пределах Европейского Союза\nи могут быть переданы только в страны, которые соответствуют \nстандартам защиты, установленным Европейской Комиссией.\n\n<b>5. Удаление персональных данных</b>\n\nВы можете удалить свои данные, заблокировав наш Telegram-\nбот — это запустит автоматическое удаление данных.\nНекоторые данные могут храниться до 30 дней.\n\n<b>6. Изменения в Политике конфиденциальности</b>\n\nЭта Политика конфиденциальности может измениться в любое \nвремя. Чтобы просмотреть нашу текущую Политику \nконфиденциальности, отправьте команду /privacy.',parse_mode='HTML',reply_markup=main_menu())
@router.message(Command('reshebnik'))
async def reshebnik_mod(message:Message):

    await message.answer('Пришли задание:\n💬 напиши его текстом (рекомендуется)\n📸 или можешь отправить фото задания прямо из учебника /\nтетради\n🗣 или отправь задание голосовым сообщением\n\n❗️Важно: один запрос = одно упражнение/задание', reply_markup=main_menu_only())





















@router.callback_query(F.data == 'buy_answer')
async def money_key(callback:CallbackQuery):
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
async def money_key(callback:CallbackQuery):
    prices = [LabeledPrice(label=Currency, amount=250)]
    db = SessionLocal()

    # 1. Проверяем существующего пользователя
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()
    if user.premium is True:
       await callback.message.answer('У вас уже есть подписка 💎Premium')
       return
    db.close()


    await callback.message.answer_invoice(
        title='Покупка 💎Premium для бота',
        description='Купить ответы для 💰 бота Reshebnik',
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
    db = SessionLocal()

    # 1. Проверяем существующего пользователя
    user = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()
    user.premium = True
    db.commit()
    db.close()

    await message.answer(
            f'✅ Вы получили премиум ⭐ на месяц.\n'
            f'ID оплаты: {message.successful_payment.telegram_payment_charge_id}',
            message_effect_id="5104841245755180586"
        )







@router.callback_query(F.data == 'settings_data')
async def setting_data_get(callback:CallbackQuery):
    await callback.message.answer('<b>⚙️ Настройки</b>\n\nТариф: 🆓 Free\n\nОтветы: ⚡️ 3\n\n🆓 Ответы за друзей: 💰 0 USD₮\n\n🌎 Язык ответов: 🇷🇺 Russian', parse_mode='HTML', reply_markup=settings_reply())


@router.callback_query(F.data =='generate_picture')
async def generate_pictures(callback:CallbackQuery,state:FSMContext):
    db = SessionLocal()

    # 1. Проверяем существующего пользователя
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()
    premium_by_user = user.premium

    db.close()
    if premium_by_user is True or callback.from_user.id == ADMIN_ID:
       await state.set_state(Generate.prompt)
       await callback.message.answer('🔃 Введите текст для генерации изображения ')
       await callback.answer('')
       return
    else:

        await callback.message.answer('❌ У вас нет 💎Premium купите премиум. ')
        await callback.answer('')
        await state.clear()

@router.message(Generate.prompt)
async def generaing_picture(message:Message,state:FSMContext):
    prompt = message.text.strip()
    await message.answer("🔄 Генерация...")

    img = requests.get(f"https://image.pollinations.ai/prompt/{prompt}").content
    try:
        # Пробуем OpenAI
        r = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": "Bearer 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"},
            json={"model": "dall-e-3", "prompt": prompt}
        )

        if r.status_code == 200:
            url = r.json()["data"][0]["url"]
            img_data = requests.get(url).content

            # Сохраняем в буфер и отправляем

            await message.answer_photo(BufferedInputFile(img_data, "dalle3.png"))


        elif "unsupported_country" in r.text:
            await message.answer("⚠️ OpenAI заблокирован, использую Pollinations")



    except Exception as e:
        print(f"❌ Ошибка: {e}")

    await message.answer_photo(BufferedInputFile(img, "img.png"),caption=f'<b>Ваш Промпт:</b> {prompt}\n\n✅ Вот ваша фотография {message.from_user.first_name}',parse_mode='HTML',reply_markup=main_menu_settings())
    await state.clear()


@router.callback_query(F.data == 'main_menu_call')
async def main_menu_call(callback:CallbackQuery):
  await callback.answer('')
  await callback.message.answer('Привет! 👋 Я — умный бот Решебник!\n\n<b>Что я умею:</b>\n✍️ Решаю задачи любой сложности\n📸 Понимаю фото из учебника и голосовые сообщения              \n💡 Пишу сочинения, рефераты и эссе\n🧮 Работаю с математическими формулами\n\n<b>Лайфхаки для лучшего результата:</b>\n• Делай четкие фото при хорошем свете\n• Выбери нужный язык в настройках\n• Уточняй номер задания на фото\n• Пиши после ответа доп.вопросы, если нужно больше\nинформации\n• Жми "Новое задание" для следующей задачи\n\nПогнали! Скидывай свое задание 🚀',parse_mode='HTML',reply_markup=profile_menu())

@router.callback_query(F.data == 'new_task')
async def new_task(callback:CallbackQuery):
    await callback.answer('')
    await callback.message.answer('Пришли задание:\n💬 напиши его текстом (рекомендуется)\n📸 или можешь отправить фото задания прямо из учебника /\nтетради\n🗣 или отправь задание голосовым сообщением\n\n❗️Важно: один запрос = одно упражнение/задание',reply_markup=main_menu_only())

@router.callback_query(F.data == 'profile')
async def profile(callback:CallbackQuery):
  await callback.answer('')
  db = SessionLocal()

  # 1. Проверяем существующего пользователя
  user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()
  premium_by_us = user.premium
  user_register_at = user.register_at
  db.close()
  if premium_by_us is True:
      premium_by_us = '✅'
  else:
      premium_by_us = '❌'
  text_bot = f'ℹ️ Вся необходимая информация о вашем профиле\n\n🏷️ <b>Имя:</b> <a href="tg://copy?text=ddddd">{callback.from_user.full_name}</a>\n🔗<b>Username:</b> @{callback.from_user.username}\n\n🆔 <b>Мой ID:</b> <a href="tg://copy?text=ddddddd">6947365047</a>\n📆 <b>Регистрация:</b> <a href="tg://copy?text=fdddd">{user_register_at}</a>\n🔃 <b>TG Премиум:</b> {callback.from_user.is_premium}\n🧮 <b>Купленные запросы:</b> <a href="tg://copy?text=dddd">0</a>\n\n🔑 <b>Подписка:</b> {premium_by_us}\n🗣️ <b>Язык:</b> <b>{callback.from_user.language_code}</b>\n\n💰 Твой баланс: <a href="tg://copy?text=0.00">0.00 RUB</a>\n'
  await callback.message.answer(f'{text_bot}',parse_mode='HTML',reply_markup=main_menu_settings())

@router.message(F.content_type == ContentType.PHOTO)
async def photo_answer(message:Message):

  think_message = await message.answer('🤖 Думаю...')
  photo_id = message.photo[-1].file_id
  photo_file = await bot.get_file(photo_id)
  file_path = f"temp_{photo_id}.png"
  await bot.download_file(photo_file.file_path, file_path)

  with Image.open(file_path) as img:
    reader = easyocr.Reader(['ru', 'en'] ,gpu=False)
    result = reader.readtext(file_path, paragraph=True, detail=0)

  text_to_ai = f'Помоги решить задание:{result}'

  response_txt = await generate(text_to_ai)

  await think_message.edit_text(f' ✅ <b>Ответ готов!</b>\n\n{response_txt.replace('**','')}\n\n<b>Задавай вопросы 😄 еще!</b>',parse_mode='HTML')
  os.remove(file_path)


#startswith('Решебник')
@router.message(F.text)
async def text_ai(message:Message):
    think_message = await message.answer('🤖 Думаю...')
    text = message.text
    words = text.split()
    if len(words) <= 1:
       await message.answer("Сообщение должно содержать вопрос")
       return


    remaining_text = ' '.join(words[1:])

    text_to_ai = f'Помоги решить задание:{remaining_text}'
    response_txt = await generate(text_to_ai)


    await think_message.edit_text(f' ✅ <b>Ответ готов!</b>\n\n{response_txt.replace('**','')}\n\n<b>Задавай вопросы 😄 еще!</b>',parse_mode='HTML')







