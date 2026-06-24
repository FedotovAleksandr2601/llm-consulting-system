import httpx

from app.core.config import settings


class OpenRouterError(Exception):
    pass


SYSTEM_PROMPT = (
    "Ты полезный Telegram-бот. "
    "Отвечай кратко, понятно и только на русском языке. "
    "Не больше 4 коротких предложений. "
    "Не используй markdown, таблицы, заголовки, списки и код. "
    "Не утверждай конкретную модель или компанию-разработчика, если это не было явно указано пользователем. "
    "Если вопрос о твоём устройстве, отвечай нейтрально: ты бот, который использует внешнюю LLM через OpenRouter."
)


async def call_openrouter(prompt: str) -> str:
    url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": settings.OPENROUTER_SITE_URL,
        "X-Title": settings.OPENROUTER_APP_NAME,
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise OpenRouterError(f"Network error while calling OpenRouter: {exc}") from exc

    if response.status_code != 200:
        raise OpenRouterError(
            f"OpenRouter returned status {response.status_code}: {response.text}"
        )

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("Invalid OpenRouter response format") from exc