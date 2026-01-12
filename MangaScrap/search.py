from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from psycopg2.extensions import cursor as Cursor
from database import *
from security import *
from typing import Optional

templates = Jinja2Templates(directory="templates")

def search_func(app):
    @app.post("/search")
    def search_mangas(
        request: Request,
        query: Optional[str] = Form(None),
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        cursor.execute("""
            SELECT *
            FROM MangaNames
            WHERE search_vector @@ plainto_tsquery('english', %s)
            AND user_id = %s
        """, (query, user_id))
        manga_data = cursor.fetchall()

        return templates.TemplateResponse("library_page.html", {"request": request, "manga_data": manga_data})
