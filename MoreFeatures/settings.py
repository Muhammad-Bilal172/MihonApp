from fastapi import Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from database import *
from security import *
from typing import Optional

templates = Jinja2Templates(directory="templates")

def setting_func(app):
    @app.get("/settings")
    def settings(
        request: Request,
        user_id: str = Depends(get_current_user_uuid)
    ):
        theme = request.cookies.get("theme")

        return templates.TemplateResponse("settings.html", {"request": request, "user_id": user_id, "theme": theme})

    