import asyncio
import logging

from aiogram.dispatcher.dispatcher import BackoffConfig
from aiogram.exceptions import TelegramNetworkError

from app.bot.dispatcher import create_bot, create_dispatcher


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


async def main() -> None:
    bot = create_bot()
    dp = create_dispatcher()

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(
            bot,
            polling_timeout=30,
            handle_as_tasks=True,
            backoff_config=BackoffConfig(
                min_delay=1.0,
                max_delay=15.0,
                factor=2.0,
                jitter=0.1,
            ),
            close_bot_session=True,
        )
    except TelegramNetworkError:
        logging.exception("Telegram network error while polling")
        raise


if __name__ == "__main__":
    asyncio.run(main())