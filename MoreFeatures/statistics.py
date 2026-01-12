from fastapi import Depends, Request
from psycopg2.extensions import cursor as Cursor
from fastapi.templating import Jinja2Templates
from security import *
from database import *

templates = Jinja2Templates(directory="templates")

def get_statistics_func(app):

    @app.get("/statistics")
    def statistics(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")
        
        cursor.execute("SELECT manga_id FROM library WHERE user_id = %s", (user_id,))
        all_manga_ids = cursor.fetchall()
        library_manga_count = len(all_manga_ids)

        cursor.execute("SELECT * FROM MangaChapters WHERE user_id = %s AND manga_id IN %s", (user_id, tuple([i[0] for i in all_manga_ids])))
        chapters = cursor.fetchall()
        chapter_counts = len(chapters)

        try:
            cursor.execute("SELECT chapter_id FROM MangaImages WHERE user_id = %s", (user_id,))

        except Exception as e:
            return e

        chapter_id = cursor.fetchall()
        if chapter_id is None:
            return "No Data Found"

        try:
            cursor.execute("SELECT manga_id FROM MangaChapters WHERE user_id = %s AND chapter_id IN %s", (user_id, tuple([i[0] for i in chapter_id])))
        except Exception as e:
            return e

        manga_id = cursor.fetchall()
        if manga_id is None:
            return "No Data Found"

        cursor.execute("SELECT * FROM MangaNames WHERE manga_id IN %s AND user_id = %s", (tuple([i[0] for i in manga_id]), user_id))
        MangaData = cursor.fetchall()
        downloaded_manga_count = len(MangaData)

        return templates.TemplateResponse("statistics_page.html", {"request": request, "library_manga_count": library_manga_count, "chapter_count": chapter_counts, "downloaded_manga_count": downloaded_manga_count, "theme": theme})

        # return {"library_manga_count": library_manga_count, "chapter_count": chapter_counts, "downloaded_manga_count": downloaded_manga_count}