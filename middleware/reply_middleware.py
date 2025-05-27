from aiogram import types
from aiogram.dispatcher.middleware import BaseMiddleware

class ReplyMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        if message.reply_to_message:
            data["target_id"] = message.reply_to_message.from_user.id
        else:
            data["target_id"] = None