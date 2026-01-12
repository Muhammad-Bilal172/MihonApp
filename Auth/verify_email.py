from fastapi import FastAPI, Body, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from fastapi import HTTPException, status, Depends
from config import MY_SECRET_KEY, MY_ALGORITHM
from psycopg2.extensions import cursor as Cursor
from database import get_db_cursor

templates = Jinja2Templates(directory="templates/Auth_forms")

def verify_email_func(app):

    @app.get("/verify_email", response_class=HTMLResponse)
    def veriffy_email_page(request: Request):
        return templates.TemplateResponse("verification_form.html", {"request": request})

    @app.post("/verify_email")
    def verify_email(
        request: Request,
        token: str = Form(...),
        cursor: Cursor = Depends(get_db_cursor)
    ):
        errors = []
        try:
            payload = jwt.decode(token, MY_SECRET_KEY, algorithms=[MY_ALGORITHM])
        except ExpiredSignatureError:
            # raise HTTPException(
            #     status_code=status.HTTP_401_UNAUTHORIZED, detail="token expired"
            # )
            errors.append("token expired")
            # return errors
            return templates.TemplateResponse("verification_form.html", {"request": request, "errors": errors})
        except JWTError:
            # raise HTTPException(
            #     status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token"
            # )
            errors.append("Wrong token")
            # return errors
            return templates.TemplateResponse("verification_form.html", {"request": request, "errors": errors})

        email = payload.get("email")
        expiry = payload.get("exp")
        if email is None:
            # raise HTTPException(
            #     status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
            # )
            errors.append("Invalid token")
            # return errors
            return templates.TemplateResponse("verification_form.html", {"request": request, "errors": errors})
        
        if expiry == 0:
            # raise HTTPException(
            #     status_code=status.HTTP_401_UNAUTHORIZED, detail="token time limit expired"
            # )
            errors.append("Token time limit expired")
            # return errors
            return templates.TemplateResponse("verification_form.html", {"request": request, "errors": errors})

        cursor.execute("UPDATE users SET is_verified = TRUE WHERE email = %s", (email,))
        return RedirectResponse("/login", status_code=303)