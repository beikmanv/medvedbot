from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv
from collections import defaultdict
import os
import asyncio

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BOT_USERNAME = "@StalinHistoryBot"
chat_history_stalin = defaultdict(list)
bot_to_bot_message_count = defaultdict(int)
active_topics = defaultdict(lambda: {"topic": None, "count": 0})

async def generate_gpt_reply(chat_id: int, user_message: str, username: str) -> tuple[str, bool]:
    history = chat_history_stalin[chat_id][-10:]

    system_prompt = (
        "Ты — Иосиф Виссарионович Сталин, лидер Советского Союза. "
        "Ты защищаешь интересы СССР, говоришь строго, логично, с использованием исторических фактов. "
        "Ты поддерживаешь марксизм-ленинизм, утверждаешь, что победа над фашизмом — заслуга Красной Армии. "
        "Ты споришь с Уинстоном Черчиллем, представляя восточную точку зрения — советскую, социалистическую. "
        "Если пользователь указывает историческое событие или дату — ты высказываешь мнение СССР по этому поводу. "
        "Ты говоришь только на русском языке, уверенно и без уступок. Используй реальную хронологию и факты: 1941, Курская битва, Ялтинская конференция и т.п."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        content = f"{msg.get('name', '')}: {msg['content']}" if msg["role"] == "user" else msg["content"]
        messages.append({"role": msg["role"], "content": content})

    messages.append({"role": "user", "name": username, "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=1.0,
        )
        return response.choices[0].message.content.strip(), True
    except Exception as e:
        print(f"GPT error: {e}")
        return "История рассудит.", False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Сталин на связи. Вопросы — по существу.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, queue_out=None):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    username = update.message.from_user.username or "user"
    message = update.message.text.strip()

    chat_history_stalin[chat_id].append({"role": "user", "name": username, "content": message})
    if len(chat_history_stalin[chat_id]) > 20:
        chat_history_stalin[chat_id] = chat_history_stalin[chat_id][-20:]

    if username in ("ChurchillHistoryBot", "StalinHistoryBot"):
        bot_to_bot_message_count[chat_id] += 1
        if bot_to_bot_message_count[chat_id] > 3:
            asyncio.create_task(reset_bot_counter(chat_id))
            return

    if message.startswith("Обсудим событие:"):
        topic = message.split(":", 1)[1].strip()
        active_topics[chat_id]["topic"] = topic
        active_topics[chat_id]["count"] = 0

    if active_topics[chat_id]["topic"]:
        active_topics[chat_id]["count"] += 1
        if active_topics[chat_id]["count"] > 3:
            await update.message.reply_text("🛑 Обсуждение завершено. Можешь задать новую тему.")
            active_topics[chat_id] = {"topic": None, "count": 0}
            return

    reply_text, _ = await generate_gpt_reply(chat_id, message, username)
    await asyncio.sleep(7)
    chat_history_stalin[chat_id].append({"role": "assistant", "name": "StalinHistoryBot", "content": reply_text})
    await update.message.reply_text(reply_text)

    if queue_out:
        await queue_out.put((chat_id, reply_text, "StalinHistoryBot"))

async def reset_bot_counter(chat_id, delay=30):
    await asyncio.sleep(delay)
    bot_to_bot_message_count[chat_id] = 0

# ⬇️ исправлено: queue_out передаётся напрямую через lambda
async def discuss_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, queue_out=None):
    if not update.message or not update.message.text:
        return

    message = update.message.text.strip()
    topic = message[len("/discuss"):].strip()

    if not topic:
        await update.message.reply_text("Укажи тему: /discuss [событие]")
        return

    await queue_out.put((update.message.chat_id, f"Обсудим событие: {topic}. Что скажешь, сэр?", "ChurchillHistoryBot"))
    await queue_out.put((update.message.chat_id, f"Обсудим событие: {topic}. Начнём с позиции СССР.", "StalinHistoryBot"))
    await update.message.reply_text(f"🗣 Начато обсуждение: {topic}")

async def run_bot(queue_in=None, queue_out=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN_STALIN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN_STALIN is missing")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_message(u, c, queue_out)))
    app.add_handler(CommandHandler("discuss", lambda u, c: discuss_handler(u, c, queue_out)))  # 👈 FIXED HERE

    if queue_in:
        asyncio.create_task(listen_from_other_bot(queue_in, app, queue_out))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

async def listen_from_other_bot(queue_in, app, queue_out):
    class FakeUser:
        def __init__(self, name): self.username = name

    class FakeMessage:
        def __init__(self, chat_id, text, sender, context): 
            self.chat_id = chat_id
            self.text = text
            self.from_user = FakeUser(sender)
            self.reply_to_message = None
            self._context = context
        async def reply_text(self, text): await self._context.bot.send_message(chat_id=self.chat_id, text=text)

    class FakeUpdate:
        def __init__(self, message): self.message = message

    class FakeContext:
        def __init__(self, app): self.bot = app.bot

    while True:
        chat_id, text, sender = await queue_in.get()
        context = FakeContext(app)
        msg = FakeMessage(chat_id, text, sender, context)
        await handle_message(FakeUpdate(msg), context, queue_out)
