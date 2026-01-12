from fastapi import FastAPI, Body, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from psycopg2.extensions import cursor as Cursor
from database import get_db_cursor
from Auth.create_jwt_token import create_jwt_token
from config import *
from Auth.send_verification_code import send_verification_code_func
from models import *

templates = Jinja2Templates(directory="templates/Auth_forms")

def reset_password_func(app):

    @app.get("/forgot_password")
    def forgot_password_page(request: Request):
        return templates.TemplateResponse("forgot_password_form.html", {"request": request})

    @app.post("/forgot_password")
    def forgot_password(
        request: Request,
        email: str = Form(...),
        cursor: Cursor = Depends(get_db_cursor)
    ):
        errors = []
        try:
            cursor.execute("SELECT is_verified FROM users WHERE email = %s", (email,))
            user_verified = cursor.fetchone()[0]
            if str(user_verified).lower() == "false":
                # raise HTTPException(status_code=404, detail="User Must be verified")
                errors.append("User Must be verified")
                return templates.TemplateResponse("forgot_password_form.html", {"request": request, "errors": errors})
            forgot_token = create_jwt_token({"email": email}, 900, "access")

            text = f"Hi there! This is an email forgot token message. As according to your email {email}, \
            This is your forgot password token, \
            {forgot_token}"
            send_verification_code_func(email, text)

            # return {"forgot_token": forgot_token}
            return RedirectResponse("/reset_password", status_code=303)

        except Exception as E:
            # return {"error": E}
            errors.append(E)
            return templates.TemplateResponse("forgot_password_form.html", {"request": request, "errors": errors})
        