from aiogram import Dispatcher, types, Bot
from aiogram.filters import InlineQueryFilter, Text
from aiogram.utils.callback_data import CallbackData
from aiogram_inline_paginations.pagination import Paginator
from aiocache import cached
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.whisper import Whisper
from utils.photo import get_user_profile_photo
from utils.cache import cached_get_user_id

cb = CallbackData("whisper", "action", "whisper_id")

async def inline_query(query: types.InlineQuery):
    query_text = query.query.strip().replace("@XBCodebot", "").strip()
    sender_id = query.from_user.id
    async with async_session() as session:
        results = []
        if not query_text:
            results.append(
                types.InlineQueryResultArticle(
                    id="start",
                    title="* حالا یوزرنیم یا آیدی عددی گیرنده رو تایپ کن",
                    description="یوزرنیم یا آیدی عددی گیرنده را وارد کنید",
                    input_message_content=types.InputTextMessageContent(
                        message_text="لطفاً یوزرنیم یا آیدی عددی گیرنده را وارد کنید"
                    ),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton("شروع", switch_inline_query_current_chat="@XBCodebot")
                    )
                )
            )
            whispers = await session.execute(
                select(Whisper).filter_by(sender_id=sender_id).order_by(Whisper.created_at.desc())
            )
            for whisper in whispers.scalars().all():
                results.append(
                    types.InlineQueryResultArticle(
                        id=f"history_{whisper.id}",
                        title=f"نجوا به {whisper.receiver_username or whisper.receiver_id}",
                        description=f"ارسال در {whisper.created_at.strftime('%Y-%m-%d %H:%M')}",
                        thumbnail_url=whisper.photo_file_id,
                        input_message_content=types.InputTextMessageContent(
                            message_text=f"نجوا به {whisper.receiver_username or whisper.receiver_id}"
                        ),
                        reply_markup=types.InlineKeyboardMarkup().add(
                            types.InlineKeyboardButton(
                                "ارسال نجوا",
                                switch_inline_query_current_chat=f"@XBCodebot {whisper.receiver_id}"
                            )
                        )
                    )
                )
            paginator = Paginator(data=results, per_page=5)
            await query.answer(paginator.get_page(0), cache_time=0)
            return

        parts = query_text.split(" ", 1)
        if len(parts) == 1:
            recipient = parts[0]
            results.append(
                types.InlineQueryResultArticle(
                    id="enter_message",
                    title="حالا متن نجوا",
                    description=f"متن نجوا برای {recipient}",
                    input_message_content=types.InputTextMessageContent(
                        message_text=f"لطفاً متن نجوا برای {recipient} را وارد کنید"
                    ),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton(
                            "وارد کردن متن",
                            switch_inline_query_current_chat=f"@XBCodebot {recipient}"
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
                    description="فرمت نادرست. یوزرنیم یا آیدی عددی معتبر وارد کنید",
                    input_message_content=types.InputTextMessageContent(
                        message_text="فرمت نادرست. فرمت صحیح: @XBCodebot @username متن"
                    )
                )
            ], cache_time=0)
            return

        photo_file_id = await get_user_profile_photo(receiver_id, bot) if receiver_id else None
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

            keyboard = types.InlineKeyboardMarkup(row_width=3).add(
                types.InlineKeyboardButton("✍️ پاسخ", callback_data=cb.new(action="reply", whisper_id=str(whisper.id))),
                types.InlineKeyboardButton("👁 مشاهده", callback_data=cb.new(action="view", whisper_id=str(whisper.id))),
                types.InlineKeyboardButton("🗑 حذف", callback_data=cb.new(action="delete", whisper_id=str(whisper.id))),
            )
            results.append(
                types.InlineQueryResultArticle(
                    id=str(whisper_id),
                    title=f"* ارسال نجوا به {receiver_username or receiver_id}",
                    input_message_content=types.InputTextMessageContent(
                        f"نجوا به {receiver_username or receiver_id}\n```\n{secret_message}\n```",
                    parse_mode="MarkdownV2"
                    ),
                reply_markup=keyboard,
                description=f"پیام: {secret_message[:30]}..."
            )
            await query.answer(results, cache_time=0)

async def process_whisper_action(query: types.CallbackQuery, callback_data: dict):
    action = callback_data.get("action")
    whisper_id = int(callback_data["whisper_id"])
    user_id = query.from_user.id
    username = query.from_user.username.lstrip("@") if query.from_user.username else None

    async with async_session() as session:
        whisper = await session.get(Whisper, whisper_id)
        if not whisper:
            await query.answer("⌛ نجوا منقضی شده!", show_alert=True)
            return

        is_allowed = (
            user_id == whisper.sender_id or
            (whisper.receiver_username and username and username.lower() == whisper.receiver_username.lower())
            or
            (whisper.receiver_id and user_id == whisper.receiver_id)
        )

        if action == "view":
            if is_allowed:
                await query.answer(f"🔐 پیام نجوا: {whisper_id.message}", show_alert=True)
            else:
                await query.answer("⚠️ این نجوا برای شما نیست!", show_alert=True)

        elif action == "reply":
            await query.answer("برای پاسخ، متن نجوا را وارد کنید", show_alert=True)
            await query.message.edit_reply_markup(
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(
                        "✍️ پاسخ",
                        switch_inline_query_current_chat=f"@XBCodebot {whisper.sender_id}"
                    )
                )
            )

        elif action == "delete":
            if user_id == whisper.sender_id:
                await session.delete(whisper)
                await session.commit()
                await query.message.delete()
                await query.answer("نجوا حذف شد!", show_alert=True)
            else:
                await query.answer("فقط فرستنده می‌تواند نجوا را حذف کند!", show_alert=True)

def register_inline_handlers(dp: Dispatcher):
    dp.inline_query()(inline_query)

def register_callback_handlers(dp: Dispatcher):
    dp.callback_query()(process_whisper_action, cb.filter())

def register_reply_handlers(dp: Dispatcher):
    dp.message(Text(startswith="@XBCodebot "))(process_reply_message)

async def process_reply_message(message: types.Message, target_id: int):
    if not message.text.startswith("@XBCodebot"):
        return
    secret_message = message.text.replace("@XBCodebot ", "").strip()
    sender_id = message.from_user.id
    receiver_id = target_id
    receiver_username = None

    async with async_session() as session:
        photo_file_id = await get_user_profile_photo(receiver_id, bot)
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
    types.InlineKeyboardButton("✍️ پاسخ", callback_data=cb.new(action="reply", whisper_id=str(whisper.id))),
    types.InlineKeyboardButton("👁 مشاهده", callback_data=cb.new(action="view", whisper_id=str(whisper.id))),
    types.InlineKeyboardButton("🗑 حذف", callback_data=cb.new(action="delete", whisper_id=str(whisper.id))),
)
await message.reply(
    f"نجوا به {receiver_id}\n\n```\n{secret_message}\n```",
    parse_mode="MarkdownV2",
    reply_markup=keyboard,
)
await message.reply(f"نجوا به {receiver_id} ارسال شد.")