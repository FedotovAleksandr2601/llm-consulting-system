import asyncio

import httpx

from app.core.config import settings
from app.infra.celery_app import celery_app
from app.services.openrouter_client import OpenRouterError, call_openrouter


async def send_telegram_message(chat_id: int, text: str) -> None:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()


@celery_app.task(name="app.tasks.llm_tasks.llm_request")
def llm_request(tg_chat_id: int, prompt: str) -> None:
    asyncio.run(_llm_request_impl(tg_chat_id, prompt))


async def _llm_request_impl(tg_chat_id: int, prompt: str) -> None:
    try:
        answer = await call_openrouter(prompt)
    except OpenRouterError as exc:
        answer = f"Ошибка при обращении к LLM: {exc}"
    except Exception as exc:
        answer = f"Непредвиденная ошибка: {exc}"

    text = (answer or "").strip()

    MAX_CHARS = 1500
    SIGNATURE = "\n\n[Ответ сгенерирован LLM через OpenRouter]"

    limit = MAX_CHARS - len(SIGNATURE)
    if len(text) > limit:
        text = text[:limit - 3].rstrip() + "..."

    text += SIGNATURE

    await send_telegram_message(tg_chat_id, text)