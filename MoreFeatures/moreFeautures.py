from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from psycopg2.extensions import cursor as Cursor
from database import *
from security import *

templates = Jinja2Templates(directory="templates")

def more_feautures_func(app):
    @app.get("/more_feautures")
    def more_feautures(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")

        return templates.TemplateResponse("more_features_page.html", {"request": request, "theme": theme})

    @app.get("/more_feautures/incognito")
    def incognito_mode(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")

        return templates.TemplateResponse("incognito_mode_page.html", {"request": request, "theme": theme})

    @app.get("/incognito_mode")
    def get_incognito_mode(
        request: Request,
        incognito_box: bool = False,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")
        
        # user_id = "90c7866c-936f-4e5e-a0cf-172a90698284"

        # cursor.execute("INSERT INTO incognito_mode (user_id) VALUES (%s)", (user_id,))

        cursor.execute("SELECT * FROM incognito_mode WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if user is None:
            if user_id is not None:
                try:
                    cursor.execute("INSERT INTO incognito_mode (user_id) VALUES (%s)", (user_id,))
                except Exception as e:
                    return e

        if incognito_box is True:
            try:
                cursor.execute("UPDATE incognito_mode SET incognito_mode = %s WHERE user_id = %s", (True, user_id))
            except Exception as e:
                return e
            return RedirectResponse("/more_feautures/incognito", status_code=303)
        else:
            try:
                cursor.execute("UPDATE incognito_mode SET incognito_mode = %s WHERE user_id = %s", (False, user_id))
            except Exception as e:
                return e
            return RedirectResponse("/more_feautures/incognito", status_code=303)


    @app.get("/more_feautures/download_only")
    def download_only_mode(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")

        return templates.TemplateResponse("download_only_mode_page.html", {"request": request, "theme": theme})

    @app.get("/download_only")
    def download_only_mode(
        request: Request,
        download_only_box: bool = False,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")
        
        cursor.execute("SELECT * FROM download_only WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if user is None:
            if user_id is not None:
                try:
                    cursor.execute("INSERT INTO download_only (user_id) VALUES (%s)", (user_id,))
                except Exception as e:
                    return e
        if download_only_box is True:
            try:
                cursor.execute("UPDATE download_only SET downloaded_only_mode = %s WHERE user_id = %s", (True, user_id))
            except Exception as e:
                return e
            return RedirectResponse("/more_feautures/download_only", status_code=303)
        else:
            try:
                cursor.execute("UPDATE download_only SET downloaded_only_mode = %s WHERE user_id = %s", (False, user_id))
            except Exception as e:
                return e
            return RedirectResponse("/more_feautures/download_only", status_code=303)


    