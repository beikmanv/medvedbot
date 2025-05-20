# telegram_bot/run_history_bots.py

from multiprocessing import Process
from telegram_bot.stalin_bot import run_bot as run_stalin
from telegram_bot.churchill_bot import run_bot as run_churchill

if __name__ == "__main__":
    p1 = Process(target=run_stalin)
    p2 = Process(target=run_churchill)

    p1.start()
    p2.start()

    p1.join()
    p2.join()
