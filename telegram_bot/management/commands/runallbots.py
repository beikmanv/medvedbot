from django.core.management.base import BaseCommand
import asyncio
from telegram_bot.bot import run_bot as run_nikola
from telegram_bot.bot2 import run_bot as run_dima
from telegram_bot.stalin_bot import run_bot as run_stalin
from telegram_bot.churchill_bot import run_bot as run_churchill

class Command(BaseCommand):
    help = "Запускает всех ботов: Никола, Дима, Сталин, Черчилль"

    def handle(self, *args, **options):
        print("🤖 Запуск всех ботов...")

        async def main():
            q1 = asyncio.Queue()
            q2 = asyncio.Queue()
            q3 = asyncio.Queue()
            q4 = asyncio.Queue()

            tasks = [
                asyncio.create_task(run_nikola(queue_in=q2, queue_out=q1)),
                asyncio.create_task(run_dima(queue_in=q1, queue_out=q2)),
                asyncio.create_task(run_stalin(queue_in=q4, queue_out=q3)),
                asyncio.create_task(run_churchill(queue_in=q3, queue_out=q4)),
            ]

            await asyncio.gather(*tasks)

        asyncio.run(main())
