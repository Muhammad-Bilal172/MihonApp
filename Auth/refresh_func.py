from fastapi import FastAPI, Depends, Request, HTTPException
from jose import JWTError, jwt, ExpiredSignatureError
from config import *
from psycopg2.extensions import cursor as Cursor
from Auth.create_jwt_token import create_jwt_token

def refresh_token_function(
    refresh_token: str,
    cursor: Cursor
) -> str:

    try:
        payload = jwt.decode(refresh_token, MY_SECRET_KEY, algorithms=[MY_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401, detail="Invalid token type"
            )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("user_id")
    email = payload.get("email")
    if not user_id or not email:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    user_row = cursor.fetchone()

    if not user_row:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_payload = {"user_id": user_id, "email": email}
    new_access_token = create_jwt_token(
        new_access_payload, expires_in=int(ACCESS_TOKEN_EXPIRE), token_type="access"
    )

    return new_access_token
