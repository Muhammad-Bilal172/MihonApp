from fastapi import FastAPI, Body, Header, HTTPException, Depends, Request, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import bcrypt
from psycopg2.extensions import cursor as Cursor
from database import get_db_cursor
from config import *
from Auth.create_jwt_token import create_jwt_token
from Auth.refresh_func import refresh_token_function
from models import *

templates = Jinja2Templates(directory="templates/Auth_forms")

def login_page(app):

    @app.get("/login")
    def login_page(request: Request):
        return templates.TemplateResponse("login_form.html", {"request": request})

    @app.post("/login")
    def login(
        response: Response,
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        email: str = Form(...),
        password: str = Form(...),
    ):
        # Single, efficient query to fetch all necessary user data
        cursor.execute("SELECT user_id, user_password FROM users WHERE user_email = %s", (email,))
        user_row = cursor.fetchone()

        # If no user is found, or if password does not match, return a generic error.
        # This prevents attackers from guessing which usernames are valid.
        if not user_row:
            return templates.TemplateResponse("login_form.html", {"request": request, "errors": "Invalid Credientials"})

        user_id, password_from_db = user_row

        if bcrypt.checkpw(password.encode("utf-8"), password_from_db.encode("utf-8")):
            # Passwords match, proceed with token generation
            user_data = {"user_id": user_id, "email": email}

            access_token = create_jwt_token(
                user_data, expires_in=int(ACCESS_TOKEN_EXPIRE), token_type="access"
            )
            refresh_token = create_jwt_token(
                user_data, expires_in=int(REFRESH_TOKEN_EXPIRE), token_type="refresh"
            )

            redirect_response = RedirectResponse("/library", status_code=303)

            redirect_response.set_cookie(
                key="access",
                value=access_token,
                httponly=True,
                secure=(ENVIRONMENT == "production"),
                samesite="lax"
            )

            redirect_response.set_cookie(
                key="refresh",
                value=refresh_token,
                httponly=True,
                secure=(ENVIRONMENT == "production"),
                samesite="lax"
            )

            return redirect_response
        else:
            # Passwords do not match
            return templates.TemplateResponse("login_form.html", {"request": request, "errors": "Invalid credentials"})

    # @app.get("/refresh")
    # def refresh_token_func(
    #     request: Request,
    #     cursor: Cursor = Depends(get_db_cursor), 
    # ):

    #     refresh_token_function(request, cursor)

        # return {
        #     "access_token": new_access_token,
        #     "token_type": "bearer",
        #     "expires_in": ACCESS_TOKEN_EXPIRE,
        # }

    