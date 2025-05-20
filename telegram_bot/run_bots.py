from multiprocessing import Process
from bot import run_bot
from bot2 import run_bot2

if __name__ == "__main__":
    p1 = Process(target=run_bot)
    p2 = Process(target=run_bot2)

    p1.start()
    p2.start()

    p1.join()
    p2.join()
