from datetime import datetime, timedelta
from jose import jwt

from helpers.config import get_settings


settings = get_settings()

SECRET_KEY = settings.SECRET_KEY     # use env variable in production
ALGORITHM = "HS256"
EXPIRES_IN_MINUTES = 60 * 24 * 7  # 7 days

def create_token(user_id):
    expire = datetime.utcnow() + timedelta(minutes=EXPIRES_IN_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None
