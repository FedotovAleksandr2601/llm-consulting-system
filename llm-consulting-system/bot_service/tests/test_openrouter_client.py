import pytest
import respx
from httpx import Response

from app.services.openrouter_client import call_openrouter


@pytest.mark.asyncio
@respx.mock
async def test_call_openrouter_returns_text():
    route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Тестовый ответ от модели"
                        }
                    }
                ]
            },
        )
    )

    result = await call_openrouter("Привет")

    assert route.called
    assert result == "Тестовый ответ от модели"