from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.jwt import ExpiredJWTError, InvalidJWTError, decode_and_validate
from app.infra.redis import get_redis
from app.tasks.llm_tasks import llm_request


router = Router(name=__name__)


def build_token_key(tg_user_id: int) -> str:
    return f"token:{tg_user_id}"


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        "Это бот с доступом к большой языковой модели по JWT-токену.\n"
        "Сначала отправьте токен командой: /token <JWT>\n"
        "Потом просто напишите вопрос и я с удовольствием вам отвечу!"
    )


@router.message(Command("token"))
async def token_handler(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Использование: /token <jwt>")
        return

    token = parts[1].strip()

    try:
        decode_and_validate(token)
    except ExpiredJWTError:
        await message.answer("Токен истёк. Получи новый токен в Auth Service.")
        return
    except InvalidJWTError:
        await message.answer("Токен невалидный. Проверь и отправь снова.")
        return

    redis = get_redis()
    key = build_token_key(message.from_user.id)
    await redis.set(key, token)

    await message.answer("Токен принят и сохранён. Теперь можешь отправить обычный текстовый запрос.")


@router.message()
async def text_handler(message: Message) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Отправь текстовый запрос.")
        return

    if text.startswith("/"):
        return

    redis = get_redis()
    key = build_token_key(message.from_user.id)
    token = await redis.get(key)

    if not token:
        await message.answer(
            "Сначала нужно авторизоваться. Получи JWT в Auth Service и отправь:\n"
            "/token <jwt>"
        )
        return

    try:
        payload = decode_and_validate(token)
    except ExpiredJWTError:
        await redis.delete(key)
        await message.answer("Сохранённый токен истёк. Получи новый JWT в Auth Service и отправь /token <jwt>.")
        return
    except InvalidJWTError:
        await redis.delete(key)
        await message.answer("Сохранённый токен невалидный. Отправь новый через /token <jwt>.")
        return

    if "sub" not in payload:
        await message.answer("Некорректный токен: отсутствует sub.")
        return

    llm_request.delay(message.chat.id, text)
    await message.answer("Запрос принят в обработку. Подожди немного, я скоро отвечу.")