# telegram_bot/management/commands/runhistorybot.py

from django.core.management.base import BaseCommand
import asyncio
from telegram_bot.stalin_bot import run_bot as run_stalin
from telegram_bot.churchill_bot import run_bot as run_churchill

class Command(BaseCommand):
    help = "Запускает исторических ботов: Сталина и Черчилля"

    def handle(self, *args, **options):
        print("🕰️ Запуск Сталина и Черчилля...")

        async def main():
            q_stalin_to_churchill = asyncio.Queue()
            q_churchill_to_stalin = asyncio.Queue()

            task1 = asyncio.create_task(run_stalin(queue_in=q_churchill_to_stalin, queue_out=q_stalin_to_churchill))
            task2 = asyncio.create_task(run_churchill(queue_in=q_stalin_to_churchill, queue_out=q_churchill_to_stalin))

            await asyncio.gather(task1, task2)

        asyncio.run(main())
