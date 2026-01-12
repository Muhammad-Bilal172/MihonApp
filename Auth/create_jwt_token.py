from jose import jwt
from datetime import datetime, timedelta
from config import *

def create_jwt_token(data: dict, expires_in: int, token_type: str):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=expires_in)
    to_encode.update({"exp": expire, "type": token_type})
    token = jwt.encode(to_encode, MY_SECRET_KEY, algorithm=MY_ALGORITHM)
    return token