import logging
import os

from aiogram import Bot, Dispatcher, executor, types
...
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
