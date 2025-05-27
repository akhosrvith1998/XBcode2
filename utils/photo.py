from aiogram import Bot
from aiocache import cached

@cached(ttl=3600)
async def get_user_profile_photo(user_id: int, bot: Bot) -> str | None:
    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        if photos.photos:
            return photos.photos[0][-1].file_id
    except Exception:
        return None