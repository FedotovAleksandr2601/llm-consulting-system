from jose import jwt

from app.core.config import settings
from app.core.jwt import ExpiredJWTError, InvalidJWTError, decode_and_validate


def test_decode_and_validate_valid_token():
    token = jwt.encode(
        {
            "sub": "1",
            "role": "user",
            "iat": 1710000000,
            "exp": 4102444800,
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )

    payload = decode_and_validate(token)

    assert payload["sub"] == "1"
    assert payload["role"] == "user"


def test_decode_and_validate_invalid_token():
    invalid_token = "not-a-real-jwt"

    try:
        decode_and_validate(invalid_token)
        assert False, "Expected InvalidJWTError"
    except InvalidJWTError:
        assert True