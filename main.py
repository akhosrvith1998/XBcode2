import asyncio
import uvloop
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from handlers.handlers import register_inline_handlers, register_callback_handlers, register_reply_handlers
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
storage = RedisStorage(redis_url=REDIS_URL)
dp = Dispatcher(storage=storage)

# تنظیمات دیتابیس
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ثبت میدل‌ور
dp.message.middleware.register(ReplyMiddleware())

# ثبت هندلرها
register_inline_handlers(dp)
register_callback_handlers(dp)
register_reply_handlers(dp)

async def on_startup(app: web.Application):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")
    print(f"وب‌هوک روی {WEBHOOK_URL}{WEBHOOK_PATH} تنظیم شد.")

async def on_shutdown(_app: web.Application):
    await bot.delete_webhook()
    await dp.storage.close()
    await engine.dispose()

def main():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

if __name__ == "__main__":
    main()