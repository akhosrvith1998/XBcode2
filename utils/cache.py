from aiocache import Cache
from aiocache.decorators import cached

cache = Cache(Cache.REDIS, endpoint="localhost", port=6379, namespace="whisper")

@cached(ttl=3600, cache=Cache.REDIS)
async def cached_get_user_id(username):
    from main import bot
    try:
        chat = await bot.get_chat(username)
        return chat.id
    except:
        return None