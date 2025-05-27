from aiocache import Cache
from aiocache.decorators import cached

cache = Cache(Cache.REDIS, endpoint="localhost", port=6379, namespace="whisper")

@cached
async def cached_get_user_id(username: str) -> int | None:
    from main import bot
    try:
        chat = await bot.get_chat(username)
        return chat.id
    except Exception:
        return None