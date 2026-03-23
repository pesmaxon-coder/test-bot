import asyncio
import logging
import sys
import os
 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
 
from config import BOT_TOKEN
from database import init_db
from handlers.registration import router as reg_router
from handlers.test import router as test_router
from handlers.settings import router as settings_router
from handlers.admin import router as admin_router
 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
 
 
async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
 
    # Admin router birinchi bo'lishi kerak
    dp.include_router(admin_router)
    dp.include_router(reg_router)
    dp.include_router(test_router)
    dp.include_router(settings_router)
 
    logging.info("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)
 
 
if __name__ == "__main__":
    asyncio.run(main())
 
