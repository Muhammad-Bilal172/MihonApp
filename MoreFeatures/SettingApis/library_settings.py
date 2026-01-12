from fastapi import Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from psycopg2.extensions import cursor as Cursor
from database import *
from security import *
from typing import Optional

templates = Jinja2Templates(directory="templates")

def library_settings_func(app):
    @app.get("/library_settings")
    def library_setting_page(
        request: Request,
        user_id: str = Depends(get_current_user_uuid),
        cursor: Cursor = Depends(get_db_cursor)
    ):
        return templates.TemplateResponse("library_settings_page.html", {"request": request})