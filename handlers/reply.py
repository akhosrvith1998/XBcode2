from aiogram import Dispatcher, types
from sqlalchemy.ext.asyncio import AsyncSession
from models.whisper import Whisper
from utils.photo import get_user_profile_photo
from aiogram.utils.callback_data import CallbackData

cb = CallbackData("whisper", "action", "whisper_id")

async def process_reply_message(message: types.Message, target_id: int):
    if not message.text.startswith("@XBCodebot "):
        return
    secret_message = message.text.replace("@XBCodebot ", "").strip()
    sender_id = message.from_user.id
    receiver_id = target_id
    receiver_username = None

    async with async_session() as session:
        photo_file_id = await get_user_profile_photo(receiver_id)
        whisper = Whisper(
            sender_id=sender_id,
            receiver_id=receiver_id,
            receiver_username=receiver_username,
            message=secret_message,
            photo_file_id=photo_file_id
        )
        session.add(whisper)
        await session.commit()

        keyboard = types.InlineKeyboardMarkup(row_width=3).add(
            types.InlineKeyboardButton("✍️ پاسخ", callback_data=cb.new(action="reply", whisper_id=whisper.id)),
            types.InlineKeyboardButton("👁 مشاهده", callback_data=cb.new(action="view", whisper_id=whisper.id)),
            types.InlineKeyboardButton("🗑 حذف", callback_data=cb.new(action="delete", whisper_id=whisper.id)),
        )
        await message.reply(
            f"نجوا به {receiver_id}\n```{secret_message}```",
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
        await message.reply(f"نجوا به {receiver_id} ارسال شد.")

def register_reply_handlers(dp: Dispatcher):
    dp.register_message_handler(process_reply_message, content_types=types.ContentTypes.TEXT, state="*")
