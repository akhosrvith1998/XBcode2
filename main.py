import asyncio
import uvloop
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.utils import executor
from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from handlers.inline import register_inline_handlers
from handlers.callback import register_callback_handlers
from handlers.reply import register_reply_handlers
from middleware.reply_middleware import ReplyMiddleware
from models.whisper import Base

# تنظیم uvloop برای بهبود عملکرد
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# بارگذاری متغیرهای محیطی
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")

# تنظیمات Bot و Dispatcher
bot = Bot(token=BOT_TOKEN)
storage = RedisStorage2(host=REDIS_URL.split("://")[1].split(":")[0], port=6379)
dp = Dispatcher(bot, storage=storage)

# تنظیمات دیتابیس
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ثبت میدل‌ور
dp.middleware.setup(ReplyMiddleware())

# ثبت هندلرها
register_inline_handlers(dp)
register_callback_handlers(dp)
register_reply_handlers(dp)

async def on_startup(_):
    # ایجاد جداول دیتابیس
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # تنظیم وب‌هوک
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    print(f"Webhook set to {WEBHOOK_URL + WEBHOOK_PATH}")

async def on_shutdown(_):
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    await engine.dispose()

if __name__ == "__main__":
    from aiogram.utils.executor import start_webhook
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
    )
