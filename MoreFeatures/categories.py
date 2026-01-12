from fastapi import Depends, Request, Form
from fastapi.responses import RedirectResponse
from psycopg2.extensions import cursor as Cursor
from fastapi.templating import Jinja2Templates
from security import *
from database import *

templates = Jinja2Templates(directory="templates")

def categories_func(app):

    @app.get("/categories")
    def categories(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        
        theme = request.cookies.get("theme")

        cursor.execute("SELECT * FROM library_categories WHERE user_id = %s", (user_id,))
        categories = cursor.fetchall()

        return templates.TemplateResponse("categories_page.html", {"request": request, "categories": categories, "theme": theme})
    
    @app.get("/create_category")
    def create_category(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")

        return templates.TemplateResponse("add_category.html", {"request": request, "theme": theme})
    
    @app.post("/create_category")
    def create_category(
        request: Request,
        category_name: str = Form(...),
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")
        
        cursor.execute("SELECT * FROM library_categories WHERE user_id = %s AND category_name = %s", (user_id, category_name))
        category = cursor.fetchone()

        if category is not None:
            return "This library category already exists"

        cursor.execute("INSERT INTO library_categories (user_id, category_name) VALUES (%s, %s)", (user_id, category_name))

        return RedirectResponse("/categories", status_code=303)