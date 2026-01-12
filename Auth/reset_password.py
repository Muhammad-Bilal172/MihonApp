from fastapi import FastAPI, Body, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from psycopg2.extensions import cursor as Cursor
from database import get_db_cursor
from Auth.create_jwt_token import create_jwt_token
from config import MY_SECRET_KEY, MY_ALGORITHM
from jose import jwt, JWTError, ExpiredSignatureError
import bcrypt
from models import *

templates = Jinja2Templates(directory="templates/Auth_forms")

def reset_pass_func(app):
    @app.get("/reset_password")
    def reset_password_page(request: Request):
        return templates.TemplateResponse("reset_password_form.html", {"request": request})

    @app.post("/reset_password")
    def reset_password(
        request: Request,
        token: str = Form(...),
        password: str = Form(...),
        cursor: Cursor = Depends(get_db_cursor),
    ):
        errors = []
        if not token:
            # raise HTTPException(status_code=401, detail="Missing Authorization header")
            errors.append("Missing Authorization header")
            return templates.TemplateResponse("reset_password_form.html", {"request": request, "errors": errors})

        try:
            payload = jwt.decode(token, MY_SECRET_KEY, algorithms=[MY_ALGORITHM])
            email = payload.get("email")
            if not email:
                # raise HTTPException(status_code=401, detail="Invalid token claims")
                errors.append("Invalid token claims")
                return templates.TemplateResponse("reset_password_form.html", {"request": request, "errors": errors})

            special_characters = [
                "!",
                "@",
                "#",
                "$",
                "%",
                "^",
                "&",
                "*",
                "(",
                ")",
                "-",
                "_",
                "=",
                "+",
                "[",
                "]",
                "{",
                "}",
                "|",
                "\\",
                ":",
                ";",
                "'",
                '"',
                "<",
                ">",
                ",",
                ".",
                "?",
                "/",
                "~",
                "`",
            ]

            for i in password:
                if i in special_characters:
                    break
            else:
                errors.append("Password must contain at least one special character")

            if len(password) < 8:
                errors.append("Password must be at least 8 characters long")

            if len(errors) > 0:
                # return {"errors": errors}
                return templates.TemplateResponse("reset_password_form.html", {"request": request, "errors": errors})

            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
            password = hashed_password.decode("utf-8")

            cursor.execute(
                "UPDATE users SET password = %s WHERE email = %s", (password, email)
            )

        except ExpiredSignatureError:
            # raise HTTPException(status_code=401, detail="Token expired")
            errors.append("Token Expired")
            return templates.TemplateResponse("reset_password_form.html", {"request": request, "errors": errors})
        except JWTError:
            # raise HTTPException(status_code=401, detail="Invalid token")
            errors.append("Invalid token")
            return templates.TemplateResponse("reset_password_form.html", {"request": request, "errors": errors})

        return RedirectResponse("/login", status_code=303)