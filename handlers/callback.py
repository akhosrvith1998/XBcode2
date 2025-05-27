from aiogram import Dispatcher, types
from aiogram.utils.callback_data import CallbackData
from sqlalchemy.ext.asyncio import AsyncSession
from models.whisper import Whisper
from sqlalchemy import select

cb = CallbackData("whisper", "action", "whisper_id")

async def process_whisper_action(query: types.CallbackQuery, callback_data: dict):
    action = callback_data["action"]
    whisper_id = int(callback_data["whisper_id"])
    user_id = query.from_user.id
    username = query.from_user.username.lstrip("@").lower() if query.from_user.username else None

    async with async_session() as session:
        whisper = await session.get(Whisper, whisper_id)
        if not whisper:
            await query.answer("⌛️ نجوا منقضی شده!", show_alert=True)
            return

        is_allowed = (
            user_id == whisper.sender_id or
            (whisper.receiver_username and username and username.lower() == whisper.receiver_username.lower()) or
            (whisper.receiver_id and user_id == whisper.receiver_id)
        )

        if action == "view":
            if is_allowed:
                await query.answer(f"🔐 پیام نجوا: {whisper.message}", show_alert=True)
            else:
                await query.answer("⚠️ این نجوا برای شما نیست!", show_alert=True)

        elif action == "reply":
            await query.answer("برای پاسخ، متن نجوا را وارد کنید", show_alert=True)
            await query.message.edit_reply_markup(
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(
                        "✍️ پاسخ",
                        switch_inline_query_current_chat=f"@XBCodebot {whisper.sender_id} "
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

def register_callback_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(process_whisper_action, cb.filter())
