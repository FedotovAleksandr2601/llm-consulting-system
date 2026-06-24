from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError, TokenExpiredError, UserNotFoundError
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.repositories.users import UsersRepository
from app.usecases.auth import AuthUseCase


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_users_repo(db: AsyncSession = Depends(get_db)) -> UsersRepository:
    return UsersRepository(db)


def get_auth_uc(users_repo: UsersRepository = Depends(get_users_repo)) -> AuthUseCase:
    return AuthUseCase(users_repo)


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError:
        raise InvalidTokenError()

    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError("Token payload does not contain 'sub'")

    try:
        return int(sub)
    except (TypeError, ValueError):
        raise InvalidTokenError("Token subject must be a valid integer user id")


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    users_repo: UsersRepository = Depends(get_users_repo),
):
    user = await users_repo.get_by_id(user_id)
    if not user:
        raise UserNotFoundError()
    return user