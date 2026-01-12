from fastapi import Request, Depends
from security import *
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

def add_extension_func(app):

    @app.get("/addExtension")
    def add_extensions(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")
        return templates.TemplateResponse("add_extensions.html", {"request": request, "theme": theme})