from fastapi import Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from psycopg2.extensions import cursor as Cursor
from database import *
from security import *
from typing import Optional

templates = Jinja2Templates(directory="templates")

def appearence_func(app):
    @app.get("/appearance")
    def appearance(
        request: Request,
        user_id: str = Depends(get_current_user_uuid),
        cursor: Cursor = Depends(get_db_cursor)
    ):
        theme = request.cookies.get("theme")

        cursor.execute("SELECT day_formatter FROM day_formatter WHERE user_id = %s", (user_id,))
        day_formatter = cursor.fetchone()

        if day_formatter is not None:
            day_formatter = day_formatter[0]
        else:
            day_formatter = "Default"

        return templates.TemplateResponse("appearance.html", {"request": request, "user_id": user_id, "theme": theme, "day_formatter": day_formatter})

    @app.post("/set_theme")
    def appearance(
        request: Request,
        system: Optional[str] = Form(None),
        dark: Optional[str] = Form(None),
        light: Optional[str] = Form(None),
        user_id: str = Depends(get_current_user_uuid)
    ):
        theme = request.cookies.get("theme")

        response = RedirectResponse("/appearance", status_code=303)
        if system:
            response.set_cookie(key="theme", value="system", httponly=True, max_age=260)
        elif dark:
            response.set_cookie(key="theme", value="dark", httponly=True, max_age=260)
        elif light:
            response.set_cookie(key="theme", value="light", httponly=True, max_age=260)

        return response

    @app.post("/get_day_formatter")
    def get_day_formatter(
        request: Request,
        date_format: Optional[str] = Form(None),
        user_id: str = Depends(get_current_user_uuid),
        cursor: Cursor = Depends(get_db_cursor)
    ):
        cursor.execute("SELECT * FROM day_formatter WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if user is None:
            cursor.execute("INSERT INTO day_formatter (user_id, day_formatter) VALUES (%s, %s)", (user_id, "Default"))

        if date_format == "Default":
            cursor.execute("UPDATE day_formatter SET day_formatter = %s WHERE user_id = %s", ("Default", user_id))

        elif date_format == "MM / DD / YYYY":
            cursor.execute("UPDATE day_formatter SET day_formatter = %s WHERE user_id = %s", ("MM / DD / YYYY", user_id))

        elif date_format == "DD / MM / YYYY":
            cursor.execute("UPDATE day_formatter SET day_formatter = %s WHERE user_id = %s", ("DD / MM / YYYY", user_id))

        elif date_format == "YYYY-MM-DD":
            cursor.execute("UPDATE day_formatter SET day_formatter = %s WHERE user_id = %s", ("YYYY-MM-DD", user_id))

        elif date_format == "DD MMM YYYY (01 Jan 2026)":
            cursor.execute("UPDATE day_formatter SET day_formatter = %s WHERE user_id = %s", ("DD MMM YYYY (01 Jan 2026)", user_id))

        elif date_format == "MMM DD, YYYY (Jan 01, 2026)":
            cursor.execute("UPDATE day_formatter SET day_formatter = %s WHERE user_id = %s", ("MMM DD, YYYY (Jan 01, 2026)", user_id))

        return RedirectResponse("/appearance", status_code=303)
    
    @app.get("/relative_timestamps")
    def relative_timestamps(
        request: Request,
        relative_timestamp_box: bool = False,
        user_id: str = Depends(get_current_user_uuid),
        cursor: Cursor = Depends(get_db_cursor)
    ):
        print(relative_timestamp_box)

        cursor.execute("SELECT * FROM relative_timestamps WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if user is None:
            cursor.execute("INSERT INTO relative_timestamps (user_id, relative_timestamp) VALUES (%s, %s)", (user_id, True))

        cursor.execute("UPDATE relative_timestamps SET relative_timestamp = %s WHERE user_id = %s", (relative_timestamp_box, user_id))        
        
        return RedirectResponse("/appearance", status_code=303)