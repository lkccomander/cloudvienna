from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from backend.config import API_JWT_ALGORITHM, API_JWT_SECRET, API_TOKEN_MINUTES


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=API_TOKEN_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, API_JWT_SECRET, algorithm=API_JWT_ALGORITHM)


def verify_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, API_JWT_SECRET, algorithms=[API_JWT_ALGORITHM])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return str(subject)

