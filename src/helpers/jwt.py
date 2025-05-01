from datetime import datetime, timedelta
from jose import ExpiredSignatureError, JWTError, jwt
from typing import Annotated
from helpers.config import get_settings
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

settings = get_settings()

SECRET_KEY = settings.SECRET_KEY     # use env variable in production
ALGORITHM = "HS256"
EXPIRES_IN_MINUTES = 60 * 24 * 7  # 7 days

def create_token(user_id):
    expire = datetime.utcnow() + timedelta(minutes=EXPIRES_IN_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return {"user_id": payload.get("sub")}  # <-- FIXED


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authentication/login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Get the current user from the token.

    Args:
        - token: The token provided by the user.

    Returns:
        - The decoded user details (e.g., user_id).

    Raises:
        - HTTPException: If the token is invalid or expired.
    """
    try:
        return decode_token(token)  # This will return a dictionary
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
