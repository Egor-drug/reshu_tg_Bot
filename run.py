import asyncio
import os
import aiohttp

# Принудительно используем ThreadedResolver вместо aiodns
try:
    aiohttp.resolver.DefaultResolver = aiohttp.resolver.ThreadedResolver
except:
    pass

from aiohttp import web
from aiogram import Bot, Dispatcher
from config import TOKEN
from app.handlers import router

async def handle(request):
    return web.Response(text="Bot is live")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(router)
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
