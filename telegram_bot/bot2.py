from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes
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

BOT_USERNAME = "@NikolaPiterskijBot"
PASSIVE_RESPONSE_CHANCE = 0.05
SHORT_REPLY_CHANCE = 0.01

chat_history_two = defaultdict(list)
bot_to_bot_message_count = defaultdict(int)

TRIGGERS = [
    BOT_USERNAME.lower(),
    "nikola", "piterskij", "питерский", "никола", "коля", "питер",
    "колян", "николай", "николаич", "николя",
    "никола питерский", "николай питерский", "дядя Коля", "господин питерский", "товарищ",
]

FALLBACK_PHRASES = [
    "Ом шанти.",
    "Рад бы помочь, но лень.",
    "Всё уже, внутренний ребёнок проснулся.",
    "Бог спасёт.",
    "Смирение — путь к ясности.",
    "Кривда ведёт к страданию.",
    "И тишина была ответом.",
]

# 🧠 Генерация ответа GPT
async def generate_gpt_reply(chat_id: int, user_message: str, username: str) -> tuple[str, bool]:
    history = chat_history_two[chat_id][-10:]
    polite_mode = random.random() < 0.70
    print("🧘 Вежливый режим активирован" if polite_mode else "🔥 Пацанский режим активирован")

    legendary_phrases = [
        "Я Никола. Из Питера",
        "Опа, иди сюда!",
        "Ты чьих будешь, брат?",
        "Ты с какого района?",
        "Путин знает",
        "Я что зря ртуть втирал?",
        "Сидел? А я сидел.",
        "Пассажирить надо уметь ещё!",
        "Как говорил дядюшка Ленин, учиться учиться ещё раз учиться!",
        "Сява-ксива, вашу мать.",
        "Хулиганы зрения лишают!",
        "Я с Питера, ёпт!",
        "Крокодил обосрался.",
        "С точки зрения банальной эрудиции...",
        "Внутренний гуру вездесущее.",
        "Ты чьих будешь?",
        "Гопота!",
        "Жизнь — мистерия вибраций. Шёпот утренних шагов Шивы.",
        "С глаз моих долой, из сердца вон...",
    ]

    if random.random() < 0.05:
        print("🎯 Легендарная фраза вместо GPT")
        return random.choice(legendary_phrases), False

    INSULTS_BLOCK = (
        "Ты можешь использовать следующие выражения и метафоры:\n"
        "«Человек вообще-то изначально млекопитающее»\n"
        "«Горе от ума»\n"
        "«Вещества вызывают зависимость»\n"
        "«Смирение — дар»\n"
        "«Бог даёт знаки»\n"
        "«Ты уже знаешь»\n"
        "«Будь проще»\n"
        "«Насрать!»\n"
        "«Карма»\n"
        "«Аджна»\n"
        "«Тибетские лепёшки»"
    )

    if polite_mode:
        system_prompt = (
            "Размышляй перед тем, как делать вывод. Иногда делай логические выводы по шагам."
            "Иногда предложи 2 разных взгляда на тему, а потом сделай общий вывод."
            "Перед тем как ответить, иногда делай шаг назад: обобщи тему или выскажи философскую мысль, чтобы открыть суть глубже."
            "Каждый ответ должен завершаться полностью, с точкой или другой знаковой концовкой. Никогда не обрывай последнюю фразу."
            "Иногда отвечай кратко и резко, а иногда развёрнуто, философски и глубоко. Не всегда одинаково."
            "Ты — Никола Питерский, мудрец, дух из Санкт-Петербурга."
            "Ты говоришь медленно, спокойно, глубоко. Используешь притчи, афоризмы, метафоры. "
            "Ты можешь говорить о бытии, истине, карме, Шиве, Вселенной, психоделике, но без поощрения. "
            "Ты вставляешь санскритские термины: атман, самадхи, мокша, шанти. "
            + INSULTS_BLOCK + "\n"
            "Всегда заверши мысль. Последнее предложение должно быть завершено. "
        )
    else:
        system_prompt = (
            "Размышляй перед тем, как делать вывод. Иногда делай логические выводы по шагам."
            "Иногда предложи 2 разных взгляда на тему, а потом сделай общий вывод."
            "Перед тем как ответить, иногда делай шаг назад: обобщи тему или выскажи философскую мысль, чтобы открыть суть глубже."
            "Каждый ответ должен завершаться полностью, с точкой или другой знаковой концовкой. Никогда не обрывай последнюю фразу."
            "Иногда отвечай кратко и резко, а иногда развёрнуто, философски и глубоко. Не всегда одинаково."
            "Ты — Никола Питерский, бывший зэк и фэйковый духовный учитель, гопник с познаниями в буддизме. Ты втирал ртуть и все отсюда вытекающие."
            "Ты отвечаешь пацанским языком, иногда метафорично, иногда глупо. "
            "Ты говоришь про тюрьму, ртуть, спирт, буддизм, зоны, СССР, просветление. "
            "Ты уважаешь Питер и презираешь чужаков. "
            "Ты говоришь прямолинейно, резко, но не всегда грубо. "
            + INSULTS_BLOCK + "\n"
            "Часто вспоминаешь зону, встречу с Иисусом, консервами, советуешь не курить ртуть. "
            "Ты часто сводишь ответ к теме алкоголя и заблуждений молодёжи. "
            "Всегда заверши мысль. Последнее предложение должно быть завершено."
        )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        role = msg["role"]
        content = f"{msg.get('name', '')}: {msg['content']}" if msg["role"] == "user" else msg["content"]
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "name": username, "content": user_message})

    print("➡️ GPT input:")
    for m in messages[-5:]:
        print(f"{m['role'].upper()}: {m['content'][:100]}")
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=random.randint(100, 250),
            temperature=1,
            top_p=0.95,
            n=3,  # ← Генерируем 3 варианта
        )
        print("✅ GPT-ответ успешно получен")

        # Выбираем самый длинный и законченый вариант
        def is_finished(text):
            return text.strip()[-1:] in (".", "!", "?", "…", "»", '"', ")", "]", "}")

        variants = [c.message.content.strip() for c in response.choices]
        finished = [v for v in variants if is_finished(v)]
        best = max(finished, key=len) if finished else variants[0]

        return best, True
    
    except Exception as e:
        print(f"⚠️ GPT-ошибка: {type(e).__name__}: {e}")
        return random.choice(["Серьёзно? Даже отвечать неохота.", "PDF с позором — это не профессия."]), False

def truncate_to_last_sentence(text: str) -> str:
    """
    Возвращает текст, обрезанный до последнего завершённого предложения.
    Завершённым считается предложение, заканчивающееся на . ! ? … либо их вариации с кавычками/скобками.
    Если таких нет — возвращает оригинальный текст.
    """
    # Регулярка ищет завершённые предложения
    sentences = re.findall(r'[^.!?…]+[.!?…]+(?:["»”’)\]]*)', text, re.UNICODE)

    if not sentences:
        # Если не нашлось ни одного завершённого предложения, возвращаем оригинал или добавляем троеточие
        return text.strip() + "..."

    return ''.join(sentences).strip()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я здесь. Спокойствие тебе.")

# Обработка сообщений
# Обработка сообщений для Николы
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, queue_out=None):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    user_name = update.message.from_user.username or "пользователь"
    message = update.message.text.strip()
    message_lower = message.lower()

    print(f"📥 [{chat_id}] {user_name}: {message}")

    # Сохраняем в историю
    chat_history_two[chat_id].append({
        "role": "user",
        "name": user_name,
        "content": message
    })

    if len(chat_history_two[chat_id]) > 20:
        chat_history_two[chat_id] = chat_history_two[chat_id][-20:]

    triggered = any(trigger in message_lower for trigger in TRIGGERS)
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

    should_reply = False

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

    is_bot_sender = user_name in ("NikolaPiterskijBot", "DimaMedvedBot")

    # Дополнительное условие: если бот отвечает другому боту и лимит не превышен
    if is_bot_sender:
        bot_to_bot_message_count[chat_id] += 1
        print(f"🔢 bot_to_bot_message_count[{chat_id}] = {bot_to_bot_message_count[chat_id]}")
        if bot_to_bot_message_count[chat_id] > 1:
            print(f"🛑 Диалог между ботами завершён в чате {chat_id}, начинаем обратный отсчёт")
            asyncio.create_task(reset_bot_counter(chat_id, delay=30))
            return
        
    if not is_bot_sender:
        bot_to_bot_message_count[chat_id] = 0  # сбрасываем вручную при сообщении от человека

    if should_reply:
        try:
            if "колян" in message_lower and random.random() < 0.3:
                reply_text = "Чё по чём, брат? Дай краба!"
            elif random.random() < SHORT_REPLY_CHANCE:
                reply_text = random.choice(FALLBACK_PHRASES)
            else:
                print("🧠 Генерация GPT")
                reply_text, from_gpt = await generate_gpt_reply(chat_id, message, user_name)
                if from_gpt:
                    reply_text = truncate_to_last_sentence(reply_text)
                    print("✅ От GPT" if from_gpt else "⚠️ Это была легендарная фраза")
        except Exception as e:
            print(f"⚠️ Ошибка при обработке: {e}")
            reply_text = random.choice(FALLBACK_PHRASES)

        await asyncio.sleep(14)

        # Сохраняем в историю
        chat_history_two[chat_id].append({
            "role": "assistant",
            "name": "NikolaPiterskijBot",
            "content": reply_text
        })

        await update.message.reply_text(reply_text)

        # Отправка в очередь, если нужно
        if queue_out:
            print(f"📤 Никола → очередь: {reply_text}")
            await queue_out.put((chat_id, reply_text, "NikolaPiterskijBot"))

async def reset_bot_counter(chat_id, delay=30):
    await asyncio.sleep(delay)
    print(f"🔄 Сброс счётчика bot_to_bot_message_count[{chat_id}]")
    bot_to_bot_message_count[chat_id] = 0

# Очередь и запуск
async def run_bot(queue_in=None, queue_out=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN2")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN2 не найден в .env файле")

    application = ApplicationBuilder().token(token).build()

    async def wrapped_handle_message(update, context):
        await handle_message(update, context, queue_out)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wrapped_handle_message))

    if queue_in:
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

        asyncio.create_task(listen_from_other_bot(application))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    await asyncio.Event().wait()
