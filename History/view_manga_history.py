from fastapi import Request, Depends
from security import *
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from psycopg2.extensions import cursor as Cursor
from database import *
from datetime import datetime, timedelta, date

templates = Jinja2Templates(directory="templates")

def view_manga_history_func(app):

    def clean_chapter_label(chapter_label: str | None) -> str | None:
        if not chapter_label:
            return chapter_label
        # Strip any trailing markers like "{S1 END}"
        return chapter_label.split("{", 1)[0].strip()

    def format_time(dt):
        return dt.strftime("%I:%M %p").lstrip("0")
    
    def format_relative_date(date_str: str, date_fmt: str):
        # Convert string to date object
        given_date = datetime.strptime(date_str, date_fmt).date()
        today = date.today()

        if given_date == today:
            return "Today"
        elif given_date == today - timedelta(days=1):
            return "Yesterday"
        else:
            return date_str

    # For viewing manga history
    @app.get("/view_manga_history")
    def view_manga_history(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        cursor.execute("SELECT day_formatter FROM day_formatter WHERE user_id = %s", (user_id,))
        day_formatter = cursor.fetchone()

        if day_formatter is not None:
            day_formatter = day_formatter[0]
        else:
            day_formatter = "Default"

        if day_formatter == "MM / DD / YYYY":
            date_fmt = "%m/%d/%Y"
        elif day_formatter == "DD / MM / YYYY":
            date_fmt = "%d/%m/%Y"
        elif day_formatter == "YYYY-MM-DD":
            date_fmt = "%Y-%m-%d"
        elif day_formatter == "DD MMM YYYY (01 Jan 2026)":
            date_fmt = "%d %b %Y"
        elif day_formatter == "MMM DD, YYYY (Jan 01, 2026)":
            date_fmt = "%b %d, %Y"
        else:
            date_fmt = "%m/%d/%Y"

        cursor.execute(
            """
            SELECT
                h.manga_id,
                h.chapter_id,
                h.created_at,
                m.title,
                m.image_url,
                COALESCE(c.chapter_number, m.chapter) AS last_read_chapter
            FROM manga_view_history h
            JOIN MangaNames m ON m.manga_id = h.manga_id
            LEFT JOIN MangaChapters c ON c.chapter_id = h.chapter_id
            WHERE h.user_id = %s
            ORDER BY h.created_at DESC
            """,
            (user_id,),
        )

        manga_history = [
            {
                "manga_id": row[0],
                "chapter_id": row[1],
                "created_at": row[2],
                "created_date": row[2].strftime(date_fmt),
                "created_time": format_time(row[2]),
                "title": row[3],
                "image_url": row[4],
                "last_read_chapter": clean_chapter_label(row[5]),
            }
            for row in cursor.fetchall()
        ]

        grouped_history = []
        for entry in manga_history:
            if not grouped_history or grouped_history[-1]["date"] != entry["created_date"]:
                grouped_history.append({"date": entry["created_date"], "entries": []})
            grouped_history[-1]["entries"].append(entry)

        theme = request.cookies.get("theme")

        cursor.execute("SELECT relative_timestamp FROM relative_timestamps WHERE user_id = %s", (user_id,))
        relative_timestamp = cursor.fetchone()

        if relative_timestamp is not None:
            relative_timestamp = relative_timestamp[0]

        if relative_timestamp:
            for i in grouped_history:
                i["date"] = format_relative_date(i["date"], date_fmt)

        return templates.TemplateResponse(
            "view_manga_history.html",
            {"request": request, "manga_data": grouped_history, "theme": theme},
        )

    @app.get("/delete_manga_history/{manga_id}")
    def delete_manga_history(
        manga_id: str,
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        # # Temporary user_id until authentication is integrated
        # user_id = "90c7866c-936f-4e5e-a0cf-172a90698284"

        cursor.execute(
            "DELETE FROM manga_view_history WHERE manga_id = %s AND user_id = %s",
            (manga_id, user_id),
        )
        return RedirectResponse("/view_manga_history", status_code=303)
