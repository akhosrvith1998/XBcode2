from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Command
from aiogram.utils.callback_data import CallbackData
from aiocache import cached
from sqlalchemy.ext.asyncio import AsyncSession
from models.whisper import Whisper
from utils.photo import get_user_profile_photo
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

async def get_user_id_from_username(bot, username):
    try:
        chat = await bot.get_chat(username)
        return chat.id
    except:
        return None

@cached(ttl=3600)
async def cached_get_user_id(username):
    return await get_user_id_from_username(bot, username)

async def inline_query(query: types.InlineQuery, dialog_manager: DialogManager):
    query_text = query.query.strip().replace("@XBCodebot", "").strip()
    sender_id = query.from_user.id
    async with async_session() as session:
        results = []
        if not query_text:
            # نمایش گزینه‌های اولیه
            results.append(
                types.InlineQueryResultArticle(
                    id="start",
                    title="* حالا یوزرنیم یا آیدی عددی گیرنده رو تایپ کن",
                    description="یوزرنیم یا آیدی عددی گیرنده را وارد کنید",
                    input_message_content=types.InputTextMessageContent(
                        message_text="لطفاً یوزرنیم یا آیدی عددی گیرنده را وارد کنید"
                    ),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton("شروع", switch_inline_query_current_chat="@XBCodebot ")
                    )
                )
            )
            # تاریخچه گیرنده‌ها
            whispers = await session.execute(
                select(Whisper).filter_by(sender_id=sender_id).order_by(Whisper.created_at.desc())
            )
            for whisper in whispers.scalars().all():
                results.append(
                    types.InlineQueryResultArticle(
                        id=f"history_{whisper.id}",
                        title=f"نجوا به {whisper.receiver_username or whisper.receiver_id}",
                        description=f"ارسال‌شده در {whisper.created_at}",
                        thumb_url=whisper.photo_file_id,
                        input_message_content=types.InputTextMessageContent(
                            message_text=f"نجوا به {whisper.receiver_username or whisper.receiver_id}"
                        ),
                        reply_markup=types.InlineKeyboardMarkup().add(
                            types.InlineKeyboardButton(
                                "ارسال نجوا",
                                switch_inline_query_current_chat=f"@XBCodebot {whisper.receiver_id} "
                            )
                        )
                    )
                )
            await query.answer(results, cache_time=0)
            return

        parts = query_text.split(" ", 1)
        if len(parts) == 1:
            recipient = parts[0]
            results.append(
                types.InlineQueryResultArticle(
                    id="enter_message",
                    title="حالا متن نجوا",
                    description=f"متن نجوا برای {recipient} را وارد کنید",
                    input_message_content=types.InputTextMessageContent(
                        message_text=f"لطفاً متن نجوا برای {recipient} را وارد کنید"
                    ),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton(
                            "وارد کردن متن",
                            switch_inline_query_current_chat=f"@XBCodebot {recipient} "
                        )
                    )
                )
            )
            await query.answer(results, cache_time=0)
            return

        receiver_id = None
        receiver_username = None
        secret_message = parts[1].strip()
        if parts[0].startswith("@"):
            receiver_username = parts[0].lstrip("@")
            receiver_id = await cached_get_user_id(receiver_username)
        elif parts[0].isdigit():
            receiver_id = int(parts[0])

        if not receiver_id and not receiver_username:
            await query.answer([
                types.InlineQueryResultArticle(
                    id="error",
                    title="خطا",
                    description="فرمت نادرست. لطفاً یوزرنیم یا آیدی عددی معتبر وارد کنید",
                    input_message_content=types.InputTextMessageContent(
                        message_text="فرمت نادرست. لطفاً یوزرنیم یا آیدی عددی معتبر وارد کنید"
                    )
                )
            ], cache_time=0)
            return

        photo_file_id = await get_user_profile_photo(receiver_id) if receiver_id else None
        async with async_session() as session:
            whisper = Whisper(
                sender_id=sender_id,
                receiver_id=receiver_id,
                receiver_username=receiver_username,
                message=secret_message,
                photo_file_id=photo_file_id
            )
            session.add(whisper)
            await session.commit()

            cb = CallbackData("whisper", "action", "whisper_id")
            keyboard = types.InlineKeyboardMarkup(row_width=3).add(
                types.InlineKeyboardButton("✍️ پاسخ", callback_data=cb.new(action="reply", whisper_id=whisper.id)),
                types.InlineKeyboardButton("👁 مشاهده", callback_data=cb.new(action="view", whisper_id=whisper.id)),
                types.InlineKeyboardButton("🗑 حذف", callback_data=cb.new(action="delete", whisper_id=whisper.id)),
            )
            results.append(
                types.InlineQueryResultArticle(
                    id=str(whisper.id),
                    title=f"* ارسال نجوا به {receiver_username or receiver_id}",
                    input_message_content=types.InputTextMessageContent(
                        message_text=f"نجوا به {receiver_username or receiver_id}\n```{secret_message}```",
                        parse_mode="MarkdownV2"
                    ),
                    reply_markup=keyboard,
                    description=f"پیام: {secret_message[:15]}..."
                )
            )
            await query.answer(results, cache_time=0)

def register_inline_handlers(dp: Dispatcher):
    dp.register_inline_handler(inline_query)
