from types import SimpleNamespace

import pytest
from jose import jwt

from app.bot import handlers
from app.core.config import settings


class FakeMessage:
    def __init__(self, text: str, user_id: int = 100, chat_id: int = 200):
        self.text = text
        self.from_user = SimpleNamespace(id=user_id)
        self.chat = SimpleNamespace(id=chat_id)
        self.answers: list[str] = []

    async def answer(self, text: str) -> None:
        self.answers.append(text)


def make_valid_token(sub: str = "1", role: str = "user") -> str:
    return jwt.encode(
        {
            "sub": sub,
            "role": role,
            "iat": 1710000000,
            "exp": 4102444800,
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )


@pytest.mark.asyncio
async def test_token_handler_saves_token(fake_redis, mocker):
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)

    token = make_valid_token()
    message = FakeMessage(text=f"/token {token}", user_id=123)

    await handlers.token_handler(message)

    saved = await fake_redis.get("token:123")
    assert saved == token
    assert any("Токен принят" in answer for answer in message.answers)


@pytest.mark.asyncio
async def test_text_handler_without_token_denies_access(fake_redis, mocker):
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    message = FakeMessage(text="Привет, бот!", user_id=123, chat_id=555)

    await handlers.text_handler(message)

    delay_mock.assert_not_called()
    assert any("Сначала нужно авторизоваться" in answer for answer in message.answers)


@pytest.mark.asyncio
async def test_text_handler_with_valid_token_calls_celery(fake_redis, mocker):
    mocker.patch("app.bot.handlers.get_redis", return_value=fake_redis)
    delay_mock = mocker.patch("app.bot.handlers.llm_request.delay")

    token = make_valid_token(sub="42")
    await fake_redis.set("token:123", token)

    message = FakeMessage(text="Объясни JWT простыми словами", user_id=123, chat_id=555)

    await handlers.text_handler(message)

    delay_mock.assert_called_once_with(555, "Объясни JWT простыми словами")
    assert any("Запрос принят" in answer for answer in message.answers)