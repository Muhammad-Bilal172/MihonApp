from fastapi import Body, Request, Depends, Form
from fastapi.responses import RedirectResponse
from psycopg2.extensions import cursor as Cursor
from fastapi.templating import Jinja2Templates
from urllib.parse import urlencode
from MangaScrap.scrapeBasicInfo import *
from database import *
from security import *

templates = Jinja2Templates(directory="templates")

def scrapePage(app):

    # For add all extensions means all websites in my website
    @app.post("/add_all_extensions")
    def scrape(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        extension_link: str = Form(...),
        user_id: str = Depends(get_current_user_uuid),
    ):

        theme = request.cookies.get("theme")

        extension_name = "Asura"

        cursor.execute("SELECT extension_link FROM installed_extensions WHERE extension_link = %s AND user_id = %s", (extension_link, user_id))
        ext_link_from_db = cursor.fetchone()

        if ext_link_from_db is not None:
            ext_link_from_db = ext_link_from_db[0]

        if extension_link == ext_link_from_db:
            return templates.TemplateResponse("add_extensions.html", {"request": request, "error": "Extension Already Exists", "theme": theme})

        MangaData = scrapeWebsites(extension_link)

        cursor.execute("INSERT INTO installed_extensions (user_id, extension_name, extension_link, search_vector) VALUES (%s, %s, %s, to_tsvector('english', %s))", (user_id, extension_name, MangaData, extension_name))

        return RedirectResponse("/all_extensions", status_code=303)

    # For showing all the available extensions means all the websites like Asura
    @app.get("/all_extensions")
    def get_all_extensions(
        request: Request,
        error: str | None = None,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")

        cursor.execute("SELECT * FROM installed_extensions WHERE user_id = %s", (user_id,))
        MangaData = cursor.fetchall()

        return templates.TemplateResponse("extensions.html", {"request": request, "manga_data": MangaData, "error": error, "theme": theme})

    # For scrape the extension like extracting the title image and rating of asura mangas
    @app.get("/scrapeMangaNames/{extension_id}")
    def scrape_manga_names(
        request: Request,
        extension_id: str,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")

        cursor.execute("SELECT * FROM MangaNames WHERE extension_id = %s AND user_id = %s", (extension_id, user_id))
        MangaData = cursor.fetchone()

        if MangaData is None:
            cursor.execute("SELECT extension_link FROM installed_extensions WHERE extension_id = %s AND user_id = %s", (extension_id, user_id))
            extension_link = cursor.fetchone()
            if extension_link is not None:
                extension_link = extension_link[0]

            MangaData = scrapeMangaMainDetails(extension_link)

            # return templates.TemplateResponse("library_page.html", {"request": request, "manga_data": MangaData, "theme": theme})

            for i in MangaData:
                cursor.execute("INSERT INTO MangaNames (user_id, extension_id, image_url, title, chapter, rating, detail_link, search_vector) VALUES (%s, %s, %s, %s, %s, %s, %s, to_tsvector('english', %s))", (user_id, extension_id, i[0], i[1], i[2], i[3], i[4], i[1]))
            return RedirectResponse("/all_extensions", status_code=303)
        params = urlencode({"error": "Extension already exists"})

        return RedirectResponse(
            url=f"/all_extensions?{params}",
            status_code=303
        )

    # For going to see all Mangas in source page
    @app.get("/all_manga/{extension_id}")
    def all_manga(
        extension_id: str,
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")
        
        cursor.execute("SELECT * FROM MangaNames WHERE extension_id = %s AND user_id = %s", (extension_id, user_id))
        MangaData = cursor.fetchall()

        return templates.TemplateResponse("library_page.html", {"request": request, "manga_data": MangaData, "theme": theme})
