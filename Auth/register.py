from fastapi import Body, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse 
from fastapi.templating import Jinja2Templates
from psycopg2.extensions import cursor as Cursor
from database import get_db_cursor
from Auth.send_verification_code import send_verification_code_func
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, status
from Auth.create_jwt_token import create_jwt_token
from models import *
import bcrypt

templates = Jinja2Templates(directory="templates/Auth_forms")
def register_page(app: FastAPI):

    # @app.get("/")
    # def main_func():
    #     return RedirectResponse("/register", status_code=303)

    @app.get("/register", response_class=HTMLResponse)
    def register_pages(request: Request):
        return templates.TemplateResponse("register_form.html", {"request": request})

    @app.post("/register")
    def register(
        request: Request,
        user: User = Body(..., embed=True),
        cursor: Cursor = Depends(get_db_cursor),
    ):

        errors = []

        special_characters = [ "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "=", "+", "[", "]",
             "{", "}", "|", "\\", ":", ";", "'", '"', "<", ">", ",", ".", "?", "/", "~", "`",
        ]

        for i in user.user_password:
            if i in special_characters:
                break
        else:
            errors.append("Password must contain at least one special character")

        if len(user.user_name) < 3:
            errors.append("Name must be at least 3 characters long")

        if "@" not in user.user_email:
            errors.append("Invalid email address")

        if "." not in user.user_email:
            errors.append("Invalid email address")

        if len(user.user_password) < 8:
            errors.append("Password must be at least 8 characters long")

        cursor.execute("SELECT user_email FROM users WHERE user_email = %s", (user.user_email,))
        row = cursor.fetchone()
        if row:
            errors.append("This account already exists")

        if len(errors) > 0:
            return templates.TemplateResponse("register_form.html", {"request": request, "errors": errors})
            # return errors

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(user.user_password.encode("utf-8"), salt)
        user.user_password = hashed_password.decode("utf-8")

        cursor.execute("INSERT INTO users (user_name, user_email, user_password, search_vector) VALUES (%s, %s, %s, to_tsvector('english', %s) || to_tsvector('english', %s)) RETURNING user_id", (user.user_name, user.user_email, user.user_password, user.user_name, user.user_email))
        user_id = cursor.fetchone()[0]

        register_token = create_jwt_token({"email": user.user_email}, 3600, "access")

        text = f"Hy, This is an registeration link for you. Please use this token \n ''{register_token}''"

        email_error = send_verification_code_func(user.user_email, text)

        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()

        if email_error is None:
            cursor.execute("INSERT INTO incognito_mode (user_id) VALUES (%s)", (user_id,))
            cursor.execute("INSERT INTO download_only (user_id) VALUES (%s)", (user_id,))
            cursor.execute("INSERT INTO library_categories (user_id, category_name) VALUES (%s, %s)", (user_id, "Default"))

            # return  {
            #     "user_id": user_data[0],
            #     "user_name": user_data[1],
            #     "name": user_data[2],
            #     "email": user_data[3],
            #     "created_at": user_data[4]
            # }
            return RedirectResponse("/verify_email", status_code=303)

        else:
            # return email_error
            return templates.TemplateResponse("register_form.html", {"request": request, "email_error": email_error})

email_rate_limit = {}

def can_resend(email: str):
    now = datetime.now()
    last_sent_time = email_rate_limit.get(email)

    if not last_sent_time:
        return True
    return (now - last_sent_time) > timedelta(minutes=1)

def resend_email_code(app: FastAPI):

    @app.get("/request_verify_email")
    def resend_verification_page(request: Request):
        return templates.TemplateResponse("request_verify_code_form.html", {"request": request})

    @app.post("/request_verify_email")
    def resend_verification(
        request: Request,
        # email: str = Form(...),
        # user: User = Form(...),
        user: User = Body(...),
        cursor: Cursor = Depends(get_db_cursor),
    ):

        cursor.execute("SELECT user_id, user_email FROM users WHERE user_email = %s", (user.user_email,))
        users = cursor.fetchone()

        errors = []

        if not users:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            # errors.append("User not found")
            # return errors
            # return templates.TemplateResponse("request_verify_code_form.html", {"request": request, "email_error": errors})

        user_id, user_email = users

        if not can_resend(user.user_email):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait at least 1 minute before requesting another verification email."
            )
            # errors.append("Please wait at least 1 minute before requesting another verification email.")
            # return errors

        verification_token = create_jwt_token({"email": user.user_email}, 3600, "access")

        text = f"Hi there! This is an email verification message. As according to your email {user.user_email}, \
            This is your verification token, \
            {verification_token}"

        email_error = send_verification_code_func(user.user_email, text)

        if email_error is None and errors is None:
            email_rate_limit[user.user_email] = datetime.now()

            # return {
            #     "email": user_email,
            #     "message": "Verification email sent successfully. Please check your inbox."
            # }
            return RedirectResponse("/verify_email", status_code=303)

        else:
            # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            #                     detail=f"Failed to send email: {email_error}")
            if email_error:
                # return email_error
                return templates.TemplateResponse("request_verify_code_form.html", {"request": request, "email_error": email_error})
            elif errors:
                # return errors
                return templates.TemplateResponse("request_verify_code_form.html", {"request": request, "email_error": errors})