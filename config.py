import os
from dotenv import load_dotenv

load_dotenv()

dbname = os.environ.get("DB_NAME")
user = os.environ.get("DB_USER")
password = os.environ.get("DB_PASSWORD")
host = os.environ.get("DB_HOST")
port = os.environ.get("DB_PORT")

MY_SECRET_KEY = os.environ.get("SECRET_KEY")
MY_ALGORITHM = os.environ.get("ALGORITHM")

ACCESS_TOKEN_EXPIRE = os.environ.get("ACCESS_TOKEN_EXPIRE")
REFRESH_TOKEN_EXPIRE = os.environ.get("REFRESH_TOKEN_EXPIRE")

smtplibPassword = os.environ.get("SMTP_PASSWORD")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
