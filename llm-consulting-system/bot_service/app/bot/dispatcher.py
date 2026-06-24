from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from app.bot.handlers import router
from app.core.config import settings


def create_bot() -> Bot:
    session = AiohttpSession(limit=10)
    return Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        session=session,
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp