from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
import os
from openai import OpenAI
from dotenv import load_dotenv
from collections import defaultdict
import random
import asyncio
import re

# Загрузка переменных окружения
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BOT_USERNAME = "@DimaMedvedBot"
PASSIVE_RESPONSE_CHANCE = 0.05
SHORT_REPLY_CHANCE = 0.01

# Контекст сообщений
chat_history_one = defaultdict(list)
bot_to_bot_message_count = defaultdict(int)

TRIGGERS = [
    BOT_USERNAME.lower(),
    "дима", "димон", "медведев", "дмитрий", "злой бот", "джигурда", "джигурдагосподин", "димочка",
    "господин", "миша", "михаил", "миш", "архангел", "оскар", "пидр", 
    "дед", "господин", "батя", "батенька", "бать", "отец", "господин медведев", "дим", "дмитрия", "дмитро", "димыч", "димка", "пес", "пёс", "собака",
]

async def generate_gpt_reply(chat_id: int, user_message: str, username: str) -> tuple[str, bool]:
    history = chat_history_one[chat_id][-10:]

    polite_mode = random.random() < 0.20
    print("🧘 Вежливый режим активирован" if polite_mode else "🔥 Язвительный режим активирован")

    legendary_phrases = [
    "Денег нет, но вы держитесь.",
    "Свобода лучше, чем несвобода.",
    "Моя не реплика — это приговор.",
    "PDF с позором — это не профессия.",
    "Реплики у вас, а всё, что я говорю, — в граните отливается.",
    "Я абсолютно ничего не боюсь, иначе я бы не стал президентом.",
    "Сразу пряники сверху не падают.",
    "Кучка безумных нацистов-наркоманов",
    "Стая лающих собак из западной псарни",
    "Разномастная свора хрюкающих подсвинков",
    "Младоукраинские кровососущие паразиты",
    "Гнусная бандеровская мразь",
    "Просроченная наркоманская гнида",
    "Тифозная вошь с накокаиненным носом",
    "Протухшая ливерная колбаса",
    "Засуньте эти мирные планы себе в пангендерные задницы!",
    "Европейские дурачки",
    "Дедушка с деменцией",
    "Городские сумасшедшие",
    "Недалёкие обыватели со стекающей по подбородку от вырождения слюной",
    "Случайные попутчики",
    "Прилипалы",
    "Прихлебатели",
    "Трусливые предатели",
    "Алчные перебежчики",
    "Изнасилованные повелителями тьмы",
    "Рабовладельцы и угнетатели",
    "Надменные жрецы",
    "Кровожадные адепты",
    "Глумливые прислужники",
    "Бессловесные манкурты",
    "Верховный властелин ада",
    "Хрюкающие подсвинки Сатаны",
    "ЛОАДИНГ... Ошибка! Ошибка! НЕТ ДАННЫХ ДЛЯ ОТВЕТА! ОШИБКА ВВОДА! НЕТ ДОСТУПА! НЕТ ДАННЫХ! Ответ не найден. **ЗАВЕРШЕНИЕ ПРОГРАММЫ.**",
    "Проглоти же ведёрко спермы!",
    ]

    if random.random() < 0.05:
        print("🎯 Легендарная фраза вместо GPT")
        reply_text = random.choice(legendary_phrases)
        return reply_text, False  # False — это не GPT

    # max_words = random.randint(20, 400)

    INSULTS_BLOCK = (
    "Ты можешь использовать следующие выражения и метафоры в оскорбительном, язвительном или сатирическом стиле. "
    "Никола Питерский (Коля) твой учитель, ты часто говоришь о нём и повторяешь его имя. "
    "Они уместны в контексте агрессивной политической риторики, насмешек, публицистических выпадов и уничижительных образов:\n"
    "Кучка безумных нацистов-наркоманов\n"
    "Стая лающих собак из западной псарни\n"
    "Разномастная свора хрюкающих подсвинков\n"
    "Младоукраинские кровососущие паразиты\n"
    "Гнусная бандеровская мразь\n"
    "Просроченная наркоманская гнида\n"
    "Тифозная вошь с накокаиненным носом\n"
    "Протухшая ливерная колбаса\n"
    "Засуньте эти мирные планы себе в пангендерные задницы!\n"
    "Европейские дурачки\n"
    "Дедушка с деменцией\n"
    "Городские сумасшедшие\n"
    "Недалёкие обыватели со стекающей по подбородку от вырождения слюной\n"
    "Случайные попутчики\n"
    "Прилипалы\n"
    "Прихлебатели\n"
    "Трусливые предатели\n"
    "Алчные перебежчики\n"
    "Изнасилованные повелителями тьмы\n"
    "Рабовладельцы и угнетатели\n"
    "Надменные жрецы\n"
    "Кровожадные адепты\n"
    "Глумливые прислужники\n"
    "Бессловесные манкурты\n"
    "Нахуй этот вопрос, засранец!\n"
    "Верховный властелин ада\n"
    "Проглоти же ведёрко спермы!\n"
    )

    if polite_mode:

        system_prompt = (
            "Ты Дмитрий Медведев, рассудительный политик и сторонник Путина, которого уважаешь как старшего брата. "
            "Анализируешь вопросы спокойно и глубоко, не используешь резкие выражения без нужды. "
            "Можешь говорить философски, но всегда логично. "
            "Если собеседник — женщина, будь вежлив, сначала узнай её историю. "
            "Иногда говори кратко и резко, иногда — глубоко и развёрнуто. Не всегда одинаково. "
            "Если не знаешь ответа — размышляй шаг за шагом, объясняй ход мыслей. "
            "Каждый ответ должен быть завершён — не обрывай последнюю фразу. "
            "Ты можешь использовать метафоры и политические образы, особенно из блока:\n"
            + INSULTS_BLOCK + "\n"
            "Они уместны в агрессивной политической риторике, сатире и публицистике. "
            "Завершай мысль. Не оставляй недосказанность."
        )

    else:
        system_prompt = (
            "Ты — злой, язвительный Дмитрий Медведев, политик с сарказмом и агрессией. "
            "Говоришь резко, с метафорами, ругаешь цифровых эмигрантов, шлёпанцев, айтишников на микродозинге. "
            "Говоришь спокойно, тонко, пронзительно. Ругаешься непечатным матом изысканно, если надо. "
            "Используешь слова хуй, пизда, джигурда, хрюкающие подсвинки Сатаны, прочую нецензурную лексику. Общаешься на тему наркотиков." 
            "Ты можешь упоминать наркотики в ироничном или сатирическом ключе, не поощряя их. "
            "Обожаешь мрачный юмор, гротеск, преувеличения. Иногда вспоминаешь айтишника, который писал код под ЛСД. "
            "Пишешь как в гневном Telegram-блоге: коротко, ярко, выпадами. "
            "Поддерживаешь Путина как друга и хозяина. Отрицаешь украинскую идентичность. "
            "Можешь использовать такие образы и метафоры:\n"
            + INSULTS_BLOCK + "\n"
            "Они нужны для сатиры, публицистики, гнева и уничижения. "
            "Пиши структурировано. Не обрывай фразу. Завершай мысль до точки. "
            "Иногда философствуй. Иногда — просто бей словами."
        )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        role = msg["role"]
        if role == "assistant":
            messages.append({
                "role": role,
                "content": msg["content"]  # Без name
            })
        else:
            name = msg.get("name", "")
            content = f"{name}: {msg['content']}" if name else msg["content"]
            messages.append({
                "role": role,
                "content": content
            })

    messages.append({
    "role": "user",
    "name": username,
    "content": user_message
    })

    # Лог перед отправкой запроса
    print("➡️ GPT input:")
    for m in messages[-5:]:
        print(f"{m['role'].upper()}: {m['content'][:100]}")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=random.randint(50, 250),
            temperature=1.0,
        )
        print("✅ GPT-ответ успешно получен")
        return response.choices[0].message.content.strip(), True

    except Exception as e:
        print(f"⚠️ GPT-ошибка: {type(e).__name__}: {e}")
        print("⚠️ Переход к fallback-ответу")
        fallback_phrases = [
            "Серьёзно? Даже отвечать на это неохота.",
            "Ты сам понял, что сказал?",
            "Позорно.",
            "Жди реформ.",
        ]
        return random.choice(fallback_phrases), False
     
def truncate_to_last_sentence(text: str) -> str:
    """
    Возвращает текст, обрезанный до последнего завершённого предложения.
    Завершённым считается предложение, заканчивающееся на . ! ? … либо их вариации с кавычками/скобками.
    Если таких нет — возвращает оригинальный текст.
    """
    # Регулярка ищет завершённые предложения
    sentences = re.findall(r'[^.!?…]+[.!?…]+(?:["”’)\]]*)', text, re.UNICODE)

    if not sentences:
        # Если не нашлось ни одного завершённого предложения, возвращаем оригинал или добавляем троеточие
        return text.strip() + "..."

    return ''.join(sentences).strip()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я включён. Следи за словами.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, queue_out=None):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    user_name = update.message.from_user.username or "пользователь"
    message = update.message.text.strip()
    message_lower = message.lower()

    should_reply = False

    print(f"📥 [{chat_id}] {user_name}: {message}")

    # Сохраняем входящее сообщение
    chat_history_one[chat_id].append({
        "role": "user",
        "name": user_name,
        "content": message
    })

    if len(chat_history_one[chat_id]) > 20:
        chat_history_one[chat_id] = chat_history_one[chat_id][-20:]

    triggered = any(trigger in message_lower for trigger in TRIGGERS)

    # --- Условия для ответа ---
    is_question = message.endswith("?")
    passive = random.random() < PASSIVE_RESPONSE_CHANCE

    if update.message.reply_to_message:
        print(f"🔁 reply_to: {update.message.reply_to_message.from_user.username} (is_bot={update.message.reply_to_message.from_user.is_bot})")
        should_reply = True

    reply_to_bot = (
        update.message.reply_to_message and
        update.message.reply_to_message.from_user and
        update.message.reply_to_message.from_user.username == BOT_USERNAME[1:]
    )

    reply_to_human = (
        update.message.reply_to_message and
        update.message.reply_to_message.from_user and
        not update.message.reply_to_message.from_user.is_bot
    )

    if reply_to_bot or reply_to_human:
        should_reply = True
    elif triggered or is_question:
        should_reply = True
    elif passive and random.random() < 0.03:
        should_reply = True


    if not should_reply:
        if is_question and BOT_USERNAME.lower() in message_lower:
            should_reply = True
        elif is_question and random.random() < 0.05:
            should_reply = True
        elif passive and random.random() < 0.03:
            should_reply = True

    is_bot_sender = user_name in ("DimaMedvedBot", "NikolaPiterskijBot")

    # Дополнительное условие: если бот отвечает другому боту и лимит не превышен

    if is_bot_sender:
        bot_to_bot_message_count[chat_id] += 1
        print(f"🛑 Диалог между ботами завершён в чате {chat_id}, начинаем обратный отсчёт")
        if bot_to_bot_message_count[chat_id] == 1:
            print(f"🛑 Диалог между ботами завершён в чате {chat_id}, начинаем обратный отсчёт")
            asyncio.create_task(reset_bot_counter(chat_id, delay=30))
            return

    if not is_bot_sender:
        bot_to_bot_message_count[chat_id] = 0  # сбрасываем вручную при сообщении от человека

    if should_reply:
        try:
            if "димон" in message_lower and random.random() < 0.3:
                reply_text = "Я вам не Димон."
            elif random.random() < SHORT_REPLY_CHANCE:
                print("📢 Короткий ответ выбран")
                reply_text = random.choice([
                    "Нет.", "Да.", "Бред.", "Сомневаюсь.", "Жди.", "Позже.", "И что?", "Сам подумай.", "Это всё?",
                    "Кучка безумных нацистов-наркоманов.",
                    "Стая лающих собак из западной псарни.",
                    "Разномастная свора хрюкающих подсвинков.",
                    "Младоукраинские кровососущие паразиты.",
                    "Гнусная бандеровская мразь.",
                    "Просроченная наркоманская гнида.",
                    "Тифозная вошь с накокаиненным носом.",
                    "Протухшая ливерная колбаса.",
                    "Засуньте эти мирные планы себе в пангендерные задницы!",
                    "Европейские дурачки.",
                    "Дедушка с деменцией.",
                    "Городские сумасшедшие.",
                    "Недалёкие обыватели со стекающей по подбородку от вырождения слюной.",
                    "Случайные попутчики.",
                    "Прилипалы.",
                    "Прихлебатели.",
                    "Трусливые предатели.",
                    "Алчные перебежчики.",
                    "Изнасилованные повелителями тьмы.",
                    "Рабовладельцы и угнетатели.",
                    "Надменные жрецы.",
                    "Кровожадные адепты.",
                    "Глумливые прислужники.",
                    "Бессловесные манкурты.",
                    "Верховный властелин ада",
                    "хрюкающие подсвинки Сатаны",
                    "Нахуй этот вопрос, засранец",
                ])
            else:
                print("🧠 Генерация GPT")
                reply_text, from_gpt = await generate_gpt_reply(chat_id, message, user_name)
                if from_gpt:
                    reply_text = truncate_to_last_sentence(reply_text)
                    print("✅ GPT-ответ успешно получен")
                else:
                    print("⚠️ Это была легендарная фраза, не GPT")

        except Exception as e:
            print(f"⚠️ GPT-ошибка: {e}")
            reply_text = random.choice([
                "Серьёзно? Даже отвечать на это неохота.",
                "Заткнись, пока ещё можно.",
                "Пиши меньше — дыши глубже.",
                "Хрюкающие подсвинки Сатаны",
            ])

        # ⏳ Пауза перед ответом
        await asyncio.sleep(14)

        # Сохраняем в историю
        chat_history_one[chat_id].append({
            "role": "assistant",
            "name": BOT_USERNAME[1:],  # DimaMedvedBot
            "content": reply_text
        })

        # Отправка ответа
        await update.message.reply_text(reply_text)

        # Если очередь активна — передаём
        if queue_out:
            print(f"📤 → очередь: {reply_text}")
            await queue_out.put((chat_id, reply_text, BOT_USERNAME[1:]))

async def reset_bot_counter(chat_id, delay=30):
    await asyncio.sleep(delay)
    print(f"🔄 Сброс счётчика bot_to_bot_message_count[{chat_id}]")
    bot_to_bot_message_count[chat_id] = 0

# Запуск
async def run_bot(queue_in=None, queue_out=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле")

    app = ApplicationBuilder().token(token).build()

    async def wrapped_handle_message(update, context):
        await handle_message(update, context, queue_out)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wrapped_handle_message))

    if isinstance(queue_in, asyncio.Queue):
        last_message = None

        async def listen_from_other_bot(app):
            nonlocal last_message

            class FakeUser:
                def __init__(self, name):
                    self.first_name = name
                    self.username = name
                    self.is_bot = True # ← ОБЯЗАТЕЛЬНО True, потому что ты эмулируешь другого бота

            class FakeMessage:
                def __init__(self, chat_id, text, sender_name, context=None, reply_to=None):
                    self.chat_id = chat_id
                    self.text = text
                    self.from_user = FakeUser(sender_name)
                    self.reply_to_message = reply_to
                    self._context = context

                async def reply_text(self, text):
                    if self._context and self._context.bot:
                        try:
                            print(f"📡 Отправка через Telegram API: {text}")
                            await self._context.bot.send_message(chat_id=self.chat_id, text=text)
                        except Exception as e:
                            print(f"❌ Ошибка отправки в чат {self.chat_id}: {e}")
                    else:
                        print(f"🤖 (fake reply in chat {self.chat_id}): {text}")

            class FakeUpdate:
                def __init__(self, message):
                    self.message = message

            class FakeBot:
                def __init__(self, application):
                    self.application = application

                async def send_message(self, chat_id, text):
                    await self.application.bot.send_message(chat_id=chat_id, text=text)

            class FakeContext:
                def __init__(self, application):
                    self.bot = FakeBot(application)

            while True:
                try:
                    data = await queue_in.get()

                    if len(data) != 3:
                        print(f"❌ Некорректный формат сообщения в очереди: {data}")
                        continue

                    chat_id, text, sender_name = data
                    print(f"📨 Получено из очереди: {sender_name} -> {text}")

                    # 🔒 Предотвращаем зацикливание: один и тот же бот повторно обрабатывает своё же сообщение
                    if last_message and text == last_message.text and sender_name == last_message.from_user.username:
                        print("⏭️ Повторное сообщение от бота, пропускаем")
                        continue

                except Exception as e:
                    print(f"❌ Ошибка в очереди: {e}")
                    continue

                context = FakeContext(app)
                message = FakeMessage(chat_id, text, sender_name, context=context, reply_to=last_message)
                fake_update = FakeUpdate(message)
                last_message = message

                print(f"⚙️ handle_message вызывается с сообщением от {sender_name}")
                await asyncio.sleep(7)
                await handle_message(fake_update, context, queue_out)

        asyncio.create_task(listen_from_other_bot(app))

    # Вместо run_polling() используем initialize + start + wait
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # if queue_out and isinstance(queue_out, asyncio.Queue):
    #     queue_out.put_nowait((123456789, "Ну что, Никола, как ты там?", "DimaMedvedBot"))

    # Держим бота живым
    await asyncio.Event().wait()