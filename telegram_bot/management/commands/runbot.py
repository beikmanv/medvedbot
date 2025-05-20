# telegram_bot/management/commands/runbot.py

from django.core.management.base import BaseCommand
import asyncio
from telegram_bot.bot import run_bot as run_nikola
from telegram_bot.bot2 import run_bot as run_dima

class Command(BaseCommand):
    help = 'Запуск двух Telegram-ботов'

    def handle(self, *args, **options):
        print("🚀 Запуск ботов...")

        async def main():
            q_nikola_to_dima = asyncio.Queue()
            q_dima_to_nikola = asyncio.Queue()

            task1 = asyncio.create_task(run_nikola(queue_in=q_dima_to_nikola, queue_out=q_nikola_to_dima))
            task2 = asyncio.create_task(run_dima(queue_in=q_nikola_to_dima, queue_out=q_dima_to_nikola))

            await asyncio.gather(task1, task2)

        asyncio.run(main())
