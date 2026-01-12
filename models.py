from pydantic import BaseModel

class User(BaseModel):
    user_name: str
    user_email: str
    user_password: str

