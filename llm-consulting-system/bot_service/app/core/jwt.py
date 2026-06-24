from datetime import datetime, timezone

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


class InvalidJWTError(Exception):
    pass


class ExpiredJWTError(Exception):
    pass


def decode_and_validate(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
        )
    except ExpiredSignatureError as exc:
        raise ExpiredJWTError("Token has expired") from exc
    except JWTError as exc:
        raise InvalidJWTError("Invalid token") from exc

    if "sub" not in payload:
        raise InvalidJWTError("Token does not contain 'sub' claim")

    if "exp" not in payload:
        raise InvalidJWTError("Token does not contain 'exp' claim")

    exp_ts = payload["exp"]
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if exp_ts < now_ts:
        raise ExpiredJWTError("Token has expired")

    return payload