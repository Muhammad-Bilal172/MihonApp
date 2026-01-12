from fastapi import Header, HTTPException, Depends, Request, Response
from jose import jwt, JWTError
from psycopg2.extensions import cursor as Cursor
from config import MY_SECRET_KEY, MY_ALGORITHM, ENVIRONMENT
from database import get_db_cursor
from datetime import datetime, timezone
from Auth.refresh_func import refresh_token_function

def get_token_expiry(token: str) -> int | int:
    try:
        payload = jwt.decode(token, MY_SECRET_KEY, algorithms=[MY_ALGORITHM], options={"verify_exp": False})
        expiry_timestamp = payload.get("exp")
        if expiry_timestamp:
            current_seconds = int(datetime.now(timezone.utc).timestamp())
            total_diff_sec = expiry_timestamp - current_seconds
            return total_diff_sec
        return -1
    except Exception as e:
        return -1

def get_current_user_uuid(
    request: Request,
    response: Response,
    cursor: Cursor = Depends(get_db_cursor)
) -> str:
    access_token = request.cookies.get("access")
    refresh_token = request.cookies.get("refresh")

    if not access_token:
        raise HTTPException(status_code=401, detail="Access token missing in cookies")

    REFRESH_THRESHOLD = 30

    try:
        payload = jwt.decode(access_token, MY_SECRET_KEY, algorithms=[MY_ALGORITHM], options={"verify_exp": False})
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")

    time_left = get_token_expiry(access_token)
    if time_left is None:
        raise HTTPException(status_code=401, detail="Invalid access token")

    if time_left <= REFRESH_THRESHOLD:
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token missing")
        
        new_access_token = refresh_token_function(refresh_token, cursor)

        request.state.new_access_token = new_access_token

        response.set_cookie(
            key="access",
            value=new_access_token,
            httponly=True,
            secure=(ENVIRONMENT == "production"),
            samesite="lax"
        )
        payload = jwt.decode(new_access_token, MY_SECRET_KEY, algorithms=[MY_ALGORITHM])
    else:
        payload = jwt.decode(
            access_token,
            MY_SECRET_KEY,
            algorithms=[MY_ALGORITHM],
        )

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    cursor.execute("SELECT user_email FROM users WHERE user_id = %s", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    return user_id
