from app.core.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.repositories.users import UsersRepository
from app.schemas.auth import RegisterRequest, TokenResponse


class AuthUseCase:
    def __init__(self, users_repo: UsersRepository):
        self.users_repo = users_repo

    async def register(self, data: RegisterRequest) -> User:
        existing_user = await self.users_repo.get_by_email(data.email)
        if existing_user:
            raise UserAlreadyExistsError()

        password_hash = hash_password(data.password)
        return await self.users_repo.create(
            email=data.email,
            password_hash=password_hash,
            role="user",
        )

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.users_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        access_token = create_access_token(
            sub=str(user.id),
            role=user.role,
        )
        return TokenResponse(access_token=access_token)

    async def me(self, user_id: int) -> User:
        user = await self.users_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return user