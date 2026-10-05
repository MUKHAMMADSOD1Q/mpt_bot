import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN, DB_PATH
from bot.database import init_db
from bot.handlers import get_root_router


async def main():
    logging.basicConfig(level=logging.INFO)

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi! .env faylini yoki hosting Variables bo'limini tekshiring.")

    # Railway Volume (masalan /data) mavjud bo'lmasa ham papka yaratilsin
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    logging.info("Baza fayli: %s", DB_PATH)

    await init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Diqqat: MemoryStorage — botni qayta ishga tushirsangiz, jarayonda turgan (yarim to'ldirilgan)
    # buyurtmalar bekor bo'ladi; foydalanuvchi /start bosib qaytadan boshlaydi. Bazadagi ma'lumotlar saqlanadi.
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(get_root_router())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
