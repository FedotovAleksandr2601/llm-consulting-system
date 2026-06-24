from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_uc, get_current_user
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.usecases.auth import AuthUseCase


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=201)
async def register(
    data: RegisterRequest,
    auth_uc: AuthUseCase = Depends(get_auth_uc),
):
    user = await auth_uc.register(data)
    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    auth_uc: AuthUseCase = Depends(get_auth_uc),
):
    return await auth_uc.login(email=form.username, password=form.password)


@router.get("/me", response_model=UserPublic)
async def me(
    current_user=Depends(get_current_user),
):
    return UserPublic.model_validate(current_user)